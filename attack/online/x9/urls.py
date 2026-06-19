#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import time

# تنظیمات
MAX_WORKERS = 20
TIMEOUT = 10
VALID_STATUS = 200

# فایل‌های استاتیک - اینارو حذف کن
STATIC_EXTENSIONS = {
    'js', 'mjs', 'cjs',
    'css', 'scss', 'sass', 'less',
    'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'webp', 'bmp', 'tiff',
    'woff', 'woff2', 'ttf', 'eot', 'otf',
    'mp4', 'mp3', 'webm', 'ogg', 'wav', 'avi', 'mov', 'flv',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'txt',
    'zip', 'rar', 'tar', 'gz', '7z',
    'json', 'xml', 'rss', 'atom',
    'map',
}

STATIC_PATHS = {
    '/static/', '/assets/', '/public/', '/dist/', '/build/',
    '/images/', '/img/', '/css/', '/js/', '/fonts/', '/media/',
    '/vendor/', '/node_modules/', '/uploads/', '/files/',
    '/wp-content/themes/', '/wp-content/plugins/',
    '/resources/', '/cdn/', '/assets/', '/bundles/',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'close'
}

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc

def find_project_root():
    current = os.path.abspath(os.getcwd())
    while current and os.path.basename(current) != "vajra":
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current

def is_static_url(url):
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    if '.' in path:
        ext = path.rsplit('.', 1)[-1]
        if ext in STATIC_EXTENSIONS:
            return True
    
    for static_path in STATIC_PATHS:
        if static_path in path:
            return True
    
    static_patterns = [
        '/favicon.', '/apple-touch-icon', '/site.webmanifest',
        '/browserconfig.xml', '/crossdomain.xml', '/humans.txt',
    ]
    for pattern in static_patterns:
        if pattern in path:
            return True
    
    return False

def has_parameters(url):
    parsed = urlparse(url)
    return bool(parsed.query)

def normalize_url_key(url):
    """
    ساخت کلید یکتا برای URL با حذف مقادیر پارامترها
    فقط نام پارامترها رو نگه میداره، نه مقادیرشون
    
    مثال:
    /post?postId=1 → /post|postId
    /post?postId=2 → /post|postId (همان کلید)
    /search?q=test&page=1 → /search|page|q
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    
    if not parsed.query:
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    
    # فقط نام پارامترها رو بگیر (مرتب شده)
    params = parse_qs(parsed.query)
    param_names = sorted(params.keys())
    param_key = '|'.join(param_names)
    
    return f"{parsed.scheme}://{parsed.netloc}{path}|{param_key}"

def keep_one_per_endpoint(urls):
    """
    برای هر endpoint (کلید یکتا)، فقط یک URL نگه میداره
    اولویت با URLای که پارامترهای بیشتری داره
    """
    grouped = defaultdict(list)
    
    for url in urls:
        key = normalize_url_key(url)
        grouped[key].append(url)
    
    result = set()
    duplicates_removed = 0
    
    for key, url_list in grouped.items():
        # URLای که پارامترهای بیشتری داره رو نگه دار
        best_url = max(url_list, key=lambda u: len(parse_qs(urlparse(u).query)))
        result.add(best_url)
        duplicates_removed += len(url_list) - 1
    
    return result, duplicates_removed

def is_interesting_url(url):
    if has_parameters(url):
        return True
    
    if is_static_url(url):
        return False
    
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    dynamic_extensions = {
        'php', 'asp', 'aspx', 'jsp', 'jspx', 'do', 'action',
        'cfm', 'cfml', 'pl', 'py', 'rb', 'cgi', 'dll', 'exe'
    }
    
    if '.' in path:
        ext = path.rsplit('.', 1)[-1]
        if ext in dynamic_extensions:
            return True
        if ext not in STATIC_EXTENSIONS:
            return True
        return False
    
    return True

def read_urls_from_files(base_dir, files):
    all_urls = set()
    
    print("\n[*] Reading URLs from files...")
    
    for file_path in files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    urls = {line.strip() for line in f if line.strip()}
                    all_urls.update(urls)
                    print(f"  ✓ {file_path} → {len(urls):,} URLs")
            except Exception as e:
                print(f"  ✗ Error reading {file_path}: {e}")
        else:
            print(f"  ⚠ Not found: {file_path}")
    
    return all_urls

def filter_interesting_urls(urls):
    interesting = set()
    static_removed = set()
    
    for url in urls:
        if is_interesting_url(url):
            interesting.add(url)
        else:
            static_removed.add(url)
    
    return interesting, static_removed

def check_url(url, domain):
    try:
        if url.startswith('/'):
            url = f"https://{domain}{url}"
        elif not url.startswith('http'):
            url = f"https://{domain}/{url}"
        
        url = url.replace(':443/', '/')
        
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=False,
            verify=False
        )
        
        return {
            'url': url,
            'status': response.status_code,
            'length': len(response.content),
            'content_type': response.headers.get('Content-Type', ''),
        }
    
    except requests.exceptions.Timeout:
        return {'url': url, 'status': 0, 'error': 'timeout'}
    except requests.exceptions.ConnectionError:
        return {'url': url, 'status': 0, 'error': 'connection'}
    except Exception as e:
        return {'url': url, 'status': 0, 'error': str(e)[:100]}

def validate_urls(urls, domain):
    valid_urls = set()
    invalid_urls = []
    stats = defaultdict(int)
    total = len(urls)
    
    print(f"\n[*] Validating {total:,} URLs...")
    print(f"[*] Workers: {MAX_WORKERS} | Timeout: {TIMEOUT}s")
    print(f"[*] Keeping only HTTP 200 OK\n")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_url, url, domain): url for url in urls}
        completed = 0
        
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            url = result['url']
            status = result['status']
            
            stats[status] += 1
            
            if completed % 50 == 0 or completed == total:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"\r  Progress: {completed}/{total} ({completed*100//total}%) "
                      f"| Valid (200): {len(valid_urls)} | Rate: {rate:.1f} req/s", end='')
            
            if status == 200:
                valid_urls.add(url)
            else:
                error = result.get('error', f'HTTP {status}')
                invalid_urls.append({
                    'url': url,
                    'status': status,
                    'reason': error
                })
    
    print()
    elapsed = time.time() - start_time
    
    return valid_urls, invalid_urls, stats, elapsed

def save_results(domain, base_dir, valid_urls, invalid_urls, static_urls, 
                 duplicates_removed, stats, elapsed):
    output_dir = os.path.join(base_dir, "attack", "online", "x9")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "urls.json")
    
    status_stats = {}
    error_stats = {}
    
    for k, v in stats.items():
        if isinstance(k, int):
            status_stats[str(k)] = v
        else:
            error_stats[k.replace('error_', '')] = v
    
    total_validated = len(valid_urls) + len(invalid_urls)
    total_urls = total_validated + len(static_urls) + duplicates_removed
    
    result = {
        'domain': domain,
        'scan_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_urls_found': total_urls,
            'static_removed': len(static_urls),
            'duplicates_removed': duplicates_removed,
            'interesting_urls': total_validated,
            'valid_urls_200': len(valid_urls),
            'invalid_urls': len(invalid_urls),
            'elapsed_seconds': round(elapsed, 2),
            'requests_per_second': round(total_validated / elapsed, 2) if elapsed > 0 else 0
        },
        'status_distribution': dict(sorted(status_stats.items(), key=lambda x: int(x[0]))),
        'errors': dict(sorted(error_stats.items())),
        'valid_urls': sorted(list(valid_urls)),
        'static_urls_removed_sample': sorted(list(static_urls))[:20],
        'invalid_urls_sample': invalid_urls[:20]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    txt_file = os.path.join(output_dir, "valid_urls.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(valid_urls)))
    
    print("\n" + "="*70)
    print(f"✅ Validation completed!")
    print("="*70)
    print(f"  Total URLs found   : {total_urls:,}")
    print(f"  Static removed     : {len(static_urls):,}")
    print(f"  Duplicates removed : {duplicates_removed:,}")
    print(f"  URLs validated     : {total_validated:,}")
    print(f"  ├─ Valid (HTTP 200): {len(valid_urls):,} ({len(valid_urls)*100//max(total_validated,1)}%)")
    print(f"  └─ Invalid         : {len(invalid_urls):,} ({len(invalid_urls)*100//max(total_validated,1)}%)")
    print(f"  Elapsed time       : {elapsed:.2f}s")
    if elapsed > 0:
        print(f"  Requests/second    : {total_validated/elapsed:.1f}")
    print("-"*70)
    if status_stats:
        print("  Status Code Distribution:")
        for code, count in sorted(status_stats.items(), key=lambda x: int(x[0])):
            print(f"    HTTP {code}: {count:,} ({count*100//max(total_validated,1)}%)")
    print("-"*70)
    print(f"  Results saved to:")
    print(f"    {output_file}")
    print(f"    {txt_file}")
    print("="*70)

def main():
    if len(sys.argv) < 2:
        target_input = input("Enter target domain (e.g. http://test.com or test.com): ").strip()
    else:
        target_input = sys.argv[1].strip()

    domain = normalize_domain(target_input)
    print(f"[*] Target domain: {domain}")

    project_root = find_project_root()
    print(f"[*] Project root: {project_root}")

    base_dir = os.path.join(project_root, "targets", domain)

    input_files = [
        "discovery/passive/wayback/wayback.txt",
        "discovery/passive/gau/gau.txt",
        "discovery/passive/sitemap/urls.txt",
        "discovery/passive/getjs/getjs_urls.txt",
        "discovery/active/katana/katana_urls.txt",
        "discovery/active/subjs/all_discovery_urls.txt",
        "discovery/active/subjs/subjs_urls.txt",
        "extraction/merge/urls-with-param.txt",
        "extraction/merge/paths-merge.txt",
        "extraction/merge/endpoints-merge.txt",
        "download/merge-urls.txt",
    ]

    all_urls = read_urls_from_files(base_dir, input_files)
    
    if not all_urls:
        print("\n❌ No URLs found!")
        return

    print(f"\n[+] Total raw URLs: {len(all_urls):,}")

    # 1. حذف استاتیک‌ها
    interesting_urls, static_urls = filter_interesting_urls(all_urls)
    
    print(f"[+] Static files removed: {len(static_urls):,}")
    
    # 2. حذف پارامترهای تکراری (نگه داشتن یکی از هر endpoint)
    unique_urls, duplicates_removed = keep_one_per_endpoint(interesting_urls)
    
    print(f"[+] Duplicate parameters removed: {duplicates_removed:,}")
    print(f"[+] Final unique URLs: {len(unique_urls):,}")
    
    if static_urls:
        print("\n[*] Sample static URLs removed:")
        for url in sorted(list(static_urls))[:3]:
            print(f"  ✗ {url}")

    if duplicates_removed > 0:
        print(f"\n[*] Removed {duplicates_removed:,} URLs with duplicate parameters")
        print(f"   Example: /post?postId=1, /post?postId=2 → kept only one")

    if not unique_urls:
        print("\n❌ No interesting URLs found!")
        return

    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    valid_urls, invalid_urls, stats, elapsed = validate_urls(unique_urls, domain)

    save_results(domain, base_dir, valid_urls, invalid_urls, static_urls, 
                 duplicates_removed, stats, elapsed)

    if valid_urls:
        print("\n[*] Sample valid URLs:")
        for url in sorted(list(valid_urls))[:10]:
            print(f"  ✓ {url}")

if __name__ == "__main__":
    main()
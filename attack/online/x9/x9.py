#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import subprocess
import os
import signal
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, unquote
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# تلاش برای import tqdm
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class X9Auto:
    # تنظیمات پیش‌فرض (می‌توانید تغییر دهید)
    GET_CHUNK_SIZE = 300          # هر قطعه چند URL داشته باشد
    POST_CHUNK_SIZE = 15           # POST تعداد درخواست بیشتری دارد
    GET_WORKERS = 20                # اجرای هم‌زمان چند قطعه GET
    POST_WORKERS = 10               # اجرای هم‌زمان قطعات POST
    CHUNK_TIMEOUT = 600            # حداکثر زمان برای هر قطعه (ثانیه)
    NUCLEI_GET_CONCURRENCY = 100   # هم‌روندی داخلی nuclei برای GET
    NUCLEI_GET_RATE = 300          # نرخ درخواست nuclei برای GET
    NUCLEI_POST_CONCURRENCY = 30   # هم‌روندی nuclei برای POST
    NUCLEI_POST_RATE = 80          # نرخ nuclei برای POST

    def __init__(self, target_url):
        self.seen_urls = set()
        self.base_dir = Path(__file__).parent
        parsed = urlparse(target_url if target_url.startswith("http") else f"https://{target_url}")
        self.domain = parsed.netloc
        self.target_url = target_url if target_url.startswith("http") else f"https://{target_url}"

        self.vajra_dir = self.base_dir.parent.parent.parent
        self.targets_dir = self.vajra_dir / "targets"
        self.output_dir = self.targets_dir / self.domain / "attack" / "online" / "x9"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.valid_urls_file = self.output_dir / "valid_urls.txt"
        self.get_urls_file = self.output_dir / "get_urls.txt"
        self.post_urls_file = self.output_dir / "post_urls.txt"
        self.result_file = self.output_dir / "result.json"
        self.debug = False

        # مدیریت قطع تمیز با Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("\n[!] Interrupted by user. Cleaning up...", file=sys.stderr)
        # پاکسازی فایل‌های موقت احتمالی
        for f in self.output_dir.glob("*_chunk_*.txt"):
            f.unlink()
        sys.exit(1)

    def load_file(self, filename):
        try:
            path = self.base_dir / filename
            with open(path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return []

    def load_valid_urls(self):
        try:
            if self.valid_urls_file.exists():
                with open(self.valid_urls_file, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
            else:
                print(f"[!] valid_urls.txt not found: {self.valid_urls_file}", file=sys.stderr)
                print(f"[!] Run urls.py first to generate valid_urls.txt", file=sys.stderr)
                return []
        except Exception as e:
            print(f"[!] Error reading valid_urls.txt: {e}", file=sys.stderr)
            return []

    def generate_get_urls_from_list(self, url_list, params, payloads):
        urls = []
        for base_url in url_list:
            parsed = urlparse(base_url)
            existing = parse_qs(parsed.query)
            existing_keys = list(existing.keys())
            test_params = existing_keys if existing_keys else params

            for payload in payloads:
                for param in test_params:
                    new_query = urlencode({param: payload})
                    url = urlunparse(parsed._replace(query=new_query))
                    if url not in self.seen_urls:
                        self.seen_urls.add(url)
                        urls.append(url)
        return urls

    def extract_payloads_from_response(self, response_body, payloads_used):
        reflected = []
        if not response_body:
            return ['mamad']
        for payload in payloads_used:
            if payload in response_body:
                reflected.append(payload)
                continue
            clean = payload.strip('"\'')
            if clean and clean in response_body:
                reflected.append(payload)
                continue
            try:
                decoded = unquote(payload)
                if decoded != payload and decoded in response_body:
                    reflected.append(payload)
                    continue
                clean_decoded = decoded.strip('"\'')
                if clean_decoded and clean_decoded != decoded and clean_decoded in response_body:
                    reflected.append(payload)
                    continue
            except:
                pass
        if not reflected and 'mamad' in response_body:
            reflected.append('mamad')
        return reflected

    def process_nuclei_output(self, lines, payloads_used, scan_type):
        findings = []
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                matched_url = data.get('matched-at', '')
                host = data.get('host', '')
                response_body = data.get('response', '')
                extracted = self.extract_payloads_from_response(response_body, payloads_used) if response_body else ['mamad']
                severity = data.get('info', {}).get('severity', 'info')
                findings.append({
                    'url': host,
                    'matched': matched_url,
                    'method': scan_type,
                    'template': data.get('template-id', ''),
                    'severity': severity,
                    'extracted': extracted,
                })
            except:
                pass
        return findings

    def run_nuclei_on_chunk(self, chunk_urls, template_path, payloads_used, scan_type, chunk_idx):
        findings = []
        chunk_file = self.output_dir / f"{scan_type.lower()}_chunk_{chunk_idx}.txt"
        with open(chunk_file, 'w') as f:
            f.write('\n'.join(chunk_urls))

        try:
            if scan_type == 'GET':
                concurrency = self.NUCLEI_GET_CONCURRENCY
                rate = self.NUCLEI_GET_RATE
            else:
                concurrency = self.NUCLEI_POST_CONCURRENCY
                rate = self.NUCLEI_POST_RATE

            cmd = [
                'nuclei',
                '-l', str(chunk_file),
                '-t', str(template_path),
                '-silent', '-jsonl', '-no-meta',
                '-timeout', '10',
                '-c', str(concurrency),
                '-rl', str(rate),
                '-bs', str(concurrency // 2)
            ]
            if self.debug:
                print(f"[DEBUG] Chunk {chunk_idx}: {' '.join(cmd)}", file=sys.stderr)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.CHUNK_TIMEOUT)
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            findings = self.process_nuclei_output(lines, payloads_used, scan_type)

        except subprocess.TimeoutExpired:
            print(f"[!] {scan_type} chunk {chunk_idx} timed out after {self.CHUNK_TIMEOUT}s, skipping", file=sys.stderr)
        except Exception as e:
            print(f"[!] {scan_type} chunk {chunk_idx} error: {e}", file=sys.stderr)
        finally:
            if chunk_file.exists():
                chunk_file.unlink()
        return findings

    def run_nuclei_with_progress(self, urls, template_path, payloads_used, scan_type):
        total = len(urls)
        if total == 0:
            return []

        chunk_size = self.GET_CHUNK_SIZE if scan_type == 'GET' else self.POST_CHUNK_SIZE
        chunks = [urls[i:i+chunk_size] for i in range(0, total, chunk_size)]
        num_chunks = len(chunks)
        workers = self.GET_WORKERS if scan_type == 'GET' else self.POST_WORKERS

        print(f"[*] {scan_type}: {total} URLs in {num_chunks} chunks (workers={workers})", file=sys.stderr)
        all_findings = []
        completed = 0

        # اجرای هم‌زمان قطعات
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for idx, chunk in enumerate(chunks, 1):
                future = executor.submit(
                    self.run_nuclei_on_chunk,
                    chunk, template_path, payloads_used, scan_type, idx
                )
                futures[future] = idx

            # نوار پیشرفت
            if TQDM_AVAILABLE:
                pbar = tqdm(total=num_chunks, desc=f"{scan_type} Progress", unit="chunk", file=sys.stderr)
            else:
                pbar = None

            for future in as_completed(futures):
                chunk_idx = futures[future]
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                except Exception as e:
                    print(f"[!] Chunk {chunk_idx} failed: {e}", file=sys.stderr)
                finally:
                    completed += 1
                    if pbar:
                        pbar.update(1)
                    else:
                        pct = completed * 100 // num_chunks
                        bar = '#' * (pct // 2) + '-' * (50 - pct // 2)
                        print(f"\r  [{bar}] {completed}/{num_chunks} chunks ({pct}%)", end='', file=sys.stderr)

            if pbar:
                pbar.close()
            else:
                print(file=sys.stderr)  # خط جدید

        print(f"[+] {scan_type} finished: {len(all_findings)} findings", file=sys.stderr)
        return all_findings

    def group_findings(self, findings):
        grouped = defaultdict(lambda: {
            'url': '', 'method': '', 'template': '', 'severity': '',
            'params_found': set(), 'reflected_payloads': set(), 'sample_urls': []
        })
        for finding in findings:
            matched_url = finding['matched']
            parsed = urlparse(matched_url)
            base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
            params = parse_qs(parsed.query)
            for param_name in params.keys():
                if param_name:
                    grouped[base_url]['params_found'].add(param_name)
            if not grouped[base_url]['url']:
                grouped[base_url]['url'] = finding['url']
                grouped[base_url]['method'] = finding['method']
                grouped[base_url]['template'] = finding['template']
                grouped[base_url]['severity'] = finding['severity']
            for payload in finding['extracted']:
                if payload and len(payload) < 100:
                    grouped[base_url]['reflected_payloads'].add(payload)
            if len(grouped[base_url]['sample_urls']) < 3:
                try:
                    decoded_url = unquote(matched_url)
                    grouped[base_url]['sample_urls'].append(decoded_url)
                except:
                    grouped[base_url]['sample_urls'].append(matched_url)

        result = []
        for base_url, data in grouped.items():
            sorted_payloads = sorted(list(data['reflected_payloads']))
            result.append({
                'url': base_url,
                'host': data['url'],
                'method': data['method'],
                'template': data['template'],
                'severity': data['severity'],
                'vulnerable_params': sorted(list(data['params_found'])),
                'reflected_payloads': sorted_payloads,
                'total_reflected': len(sorted_payloads),
                'sample_urls': data['sample_urls']
            })
        return result

    def save_results(self, target, payloads, findings, urls_from_file):
        grouped_findings = self.group_findings(findings)
        all_params = set()
        for f in grouped_findings:
            all_params.update(f['vulnerable_params'])

        result = {
            'target': target,
            'scan_info': {
                'total_urls_from_file': len(urls_from_file),
                'total_urls_tested': len(self.seen_urls),
                'payloads_count': len(payloads),
            },
            'payloads_used': payloads,
            'findings': grouped_findings,
            'summary': {
                'total_vulnerable_urls': len(grouped_findings),
                'total_reflected_payloads': sum(f['total_reflected'] for f in grouped_findings),
                'vulnerable_params': sorted(list(all_params)),
                'by_method': {},
                'by_severity': {}
            }
        }
        for f in grouped_findings:
            method = f.get('method', 'unknown')
            severity = f.get('severity', 'info')
            result['summary']['by_method'][method] = result['summary']['by_method'].get(method, 0) + 1
            result['summary']['by_severity'][severity] = result['summary']['by_severity'].get(severity, 0) + 1

        with open(self.result_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print("\n" + "="*70, file=sys.stderr)
        print(f"[+] Results saved to: {self.result_file}", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print(f"[!] URLs from file     : {len(urls_from_file)}", file=sys.stderr)
        print(f"[!] URLs tested        : {len(self.seen_urls)}", file=sys.stderr)
        print(f"[!] Vulnerable URLs    : {len(grouped_findings)}", file=sys.stderr)
        print(f"[!] Vulnerable Params  : {', '.join(sorted(all_params)) if all_params else 'None'}", file=sys.stderr)
        print(f"[!] Reflected Payloads : {result['summary']['total_reflected_payloads']}", file=sys.stderr)
        print("="*70, file=sys.stderr)

        if grouped_findings:
            print("\n[*] Detailed Findings:", file=sys.stderr)
            for idx, f in enumerate(grouped_findings, 1):
                print(f"\n  [{idx}] {f['url']}", file=sys.stderr)
                print(f"      Method: {f['method']} | Severity: {f['severity']}", file=sys.stderr)
                print(f"      Vulnerable Params: {', '.join(f['vulnerable_params'])}", file=sys.stderr)
                print(f"      Reflected Payloads ({f['total_reflected']}):", file=sys.stderr)
                for payload in f['reflected_payloads'][:10]:
                    print(f"        • {payload}", file=sys.stderr)

    def run(self, target_url):
        params = self.load_file('top29-xss.txt')
        payloads = self.load_file('payloads.txt')
        if not params:
            params = ['q', 's', 'search', 'id', 'page', 'view', 'action']
        if not payloads:
            payloads = ['mamad', '"mamad"', "'mamad'"]

        print("\n[*] Loading validated URLs from valid_urls.txt...", file=sys.stderr)
        url_list = self.load_valid_urls()
        if not url_list:
            print("[!] No validated URLs found. Run urls.py first!", file=sys.stderr)
            return

        print(f"[+] Loaded {len(url_list)} validated URLs", file=sys.stderr)
        print(f"[*] Target: {target_url}", file=sys.stderr)
        print(f"[*] Parameters to test: {len(params)}", file=sys.stderr)
        print(f"[*] Payloads: {len(payloads)}", file=sys.stderr)
        print(f"[*] Output dir: {self.output_dir}", file=sys.stderr)

        print("\n[*] Sample validated URLs:", file=sys.stderr)
        for url in url_list[:5]:
            print(f"  {url}", file=sys.stderr)
        if len(url_list) > 5:
            print(f"  ... and {len(url_list) - 5} more", file=sys.stderr)

        print("\n[*] Generating GET URLs from validated URLs...", file=sys.stderr)
        get_urls = self.generate_get_urls_from_list(url_list, params, payloads)
        with open(self.get_urls_file, 'w') as f:
            f.write('\n'.join(get_urls))
        print(f"[+] Generated {len(get_urls)} GET URLs", file=sys.stderr)
        print(f"[+] Saved to: {self.get_urls_file}", file=sys.stderr)

        post_urls = [url for url in url_list if not parse_qs(urlparse(url).query)]
        if not post_urls:
            post_urls = [target_url]
        with open(self.post_urls_file, 'w') as f:
            f.write('\n'.join(post_urls))
        print(f"[+] Saved {len(post_urls)} POST URLs", file=sys.stderr)

        print("\n[*] Sample generated GET URLs:", file=sys.stderr)
        for url in get_urls[:5]:
            print(f"  {unquote(url)[:120]}", file=sys.stderr)
        if len(get_urls) > 5:
            print(f"  ... and {len(get_urls) - 5} more", file=sys.stderr)

        # مسیرهای قالب‌ها
        get_template = self.base_dir / 'templates' / 'x9-get.yaml'
        post_template = self.base_dir / 'templates' / 'x9-post.yaml'

        print("\n" + "-"*70, file=sys.stderr)
        get_findings = self.run_nuclei_with_progress(get_urls, get_template, payloads, 'GET')

        print("-"*70, file=sys.stderr)
        post_findings = self.run_nuclei_with_progress(post_urls, post_template, payloads, 'POST')

        all_findings = get_findings + post_findings
        self.save_results(target_url, payloads, all_findings, url_list)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='X9 Auto Vulnerability Scanner')
    parser.add_argument('url', help='Target URL to scan')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--urls-file', help='Custom validated URLs file (default: valid_urls.txt)')
    args = parser.parse_args()

    x9 = X9Auto(args.url)
    if args.debug:
        x9.debug = True
    if args.urls_file:
        x9.valid_urls_file = Path(args.urls_file)

    x9.run(args.url)


if __name__ == '__main__':
    main()

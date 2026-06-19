#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import subprocess
import os
import re
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, unquote
from pathlib import Path
from collections import defaultdict


class X9Auto:
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
        
        # مسیر فایل valid_urls.txt که توسط urls.py ساخته شده
        self.valid_urls_file = self.output_dir / "valid_urls.txt"
        
        # فایل‌های خروجی
        self.get_urls_file = self.output_dir / "get_urls.txt"
        self.post_urls_file = self.output_dir / "post_urls.txt"
        self.nuclei_get_output = self.output_dir / "nuclei_get_output.jsonl"
        self.nuclei_post_output = self.output_dir / "nuclei_post_output.jsonl"
        self.result_file = self.output_dir / "result.json"
        
        self.debug = False

    def load_file(self, filename):
        try:
            path = self.base_dir / filename
            with open(path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return []

    def load_valid_urls(self):
        """خوندن URLهای معتبر از فایل valid_urls.txt"""
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
        """تولید URLهای GET از لیست URLهای معتبر"""
        urls = []
        
        for base_url in url_list:
            parsed = urlparse(base_url)
            existing = parse_qs(parsed.query)
            existing_keys = list(existing.keys())
            
            # پارامترهایی که باید تست بشن
            if existing_keys:
                # فقط پارامترهای موجود در URL رو تست کن
                test_params = existing_keys
            else:
                # اگه URL پارامتر نداره، پارامترهای پیش‌فرض رو اضافه کن
                test_params = params
            
            for payload in payloads:
                for param in test_params:
                    new_query = urlencode({param: payload})
                    url = urlunparse(parsed._replace(query=new_query))
                    if url not in self.seen_urls:
                        self.seen_urls.add(url)
                        urls.append(url)
        
        return urls

    def extract_payloads_from_response(self, response_body, payloads_used):
        """چک کردن اینکه کدوم payloadهای اصلی در response منعکس شدن"""
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
        
        if not reflected:
            if 'mamad' in response_body:
                reflected.append('mamad')
        
        return reflected

    def run_nuclei_get(self, payloads_used):
        findings = []
        
        if not self.get_urls_file.exists():
            print(f"[!] GET URLs file not found: {self.get_urls_file}", file=sys.stderr)
            return findings

        template_path = self.base_dir / 'templates' / 'x9-get.yaml'
        if not template_path.exists():
            print(f"[!] Template not found: {template_path}", file=sys.stderr)
            return findings

        print("[*] Running Nuclei on GET URLs...", file=sys.stderr)

        try:
            cmd = [
                'nuclei',
                '-l', str(self.get_urls_file),
                '-t', str(template_path),
                '-silent',
                '-jsonl',
                '-timeout', '10',
                '-c', '20',
                '-no-meta'
            ]
            
            if self.debug:
                print(f"[DEBUG] CMD: {' '.join(cmd)}", file=sys.stderr)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            output_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if self.debug:
                print(f"[DEBUG] Got {len(output_lines)} lines from nuclei stdout", file=sys.stderr)
            
            with open(self.nuclei_get_output, 'w') as f:
                f.write(result.stdout)
            
            if not output_lines:
                print(f"[!] No output from nuclei", file=sys.stderr)
                return findings
            
            for line in output_lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    matched_url = data.get('matched-at', '')
                    template_id = data.get('template-id', '')
                    host = data.get('host', '')
                    response_body = data.get('response', '')
                    
                    extracted = []
                    if response_body:
                        extracted = self.extract_payloads_from_response(response_body, payloads_used)
                    else:
                        extracted = ['mamad']
                    
                    severity = data.get('info', {}).get('severity', 'info')
                    
                    # نرمال‌سازی URL
                    parsed = urlparse(matched_url)
                    params = parse_qs(parsed.query)
                    normalized_params = {k: v[0] for k, v in params.items()}
                    normalized_query = urlencode(normalized_params)
                    normalized_url = urlunparse(parsed._replace(query=normalized_query))
                    
                    finding = {
                        'url': host,
                        'matched': normalized_url,
                        'method': 'GET',
                        'template': template_id,
                        'severity': severity,
                        'extracted': extracted,
                    }
                    
                    findings.append(finding)
                    
                except json.JSONDecodeError as e:
                    if self.debug:
                        print(f"[DEBUG] JSON error: {e}", file=sys.stderr)
                except Exception as e:
                    if self.debug:
                        print(f"[DEBUG] Parse error: {e}", file=sys.stderr)
            
            print(f"[+] GET found {len(findings)} vulnerabilities", file=sys.stderr)
            
        except Exception as e:
            print(f"[!] GET error: {e}", file=sys.stderr)
        
        return findings

    def run_nuclei_post(self, payloads_used):
        findings = []

        if not self.post_urls_file.exists():
            print(f"[!] POST URLs file not found", file=sys.stderr)
            return findings

        template_path = self.base_dir / 'templates' / 'x9-post.yaml'
        if not template_path.exists():
            print(f"[!] Template not found: {template_path}", file=sys.stderr)
            return findings

        print("[*] Running Nuclei on POST requests...", file=sys.stderr)

        try:
            cmd = [
                'nuclei',
                '-l', str(self.post_urls_file),
                '-t', str(template_path),
                '-silent',
                '-jsonl',
                '-timeout', '10',
                '-c', '20',
                '-no-meta'
            ]
            
            if self.debug:
                print(f"[DEBUG] CMD: {' '.join(cmd)}", file=sys.stderr)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            output_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            with open(self.nuclei_post_output, 'w') as f:
                f.write(result.stdout)
            
            if not output_lines:
                return findings
            
            for line in output_lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    matched_url = data.get('matched-at', '')
                    template_id = data.get('template-id', '')
                    host = data.get('host', '')
                    response_body = data.get('response', '')
                    
                    extracted = []
                    if response_body:
                        extracted = self.extract_payloads_from_response(response_body, payloads_used)
                    else:
                        extracted = ['mamad']
                    
                    severity = data.get('info', {}).get('severity', 'info')
                    
                    finding = {
                        'url': host,
                        'matched': matched_url,
                        'method': 'POST',
                        'template': template_id,
                        'severity': severity,
                        'extracted': extracted,
                    }
                    
                    findings.append(finding)
                    
                except Exception as e:
                    if self.debug:
                        print(f"[DEBUG] POST parse error: {e}", file=sys.stderr)
            
            print(f"[+] POST found {len(findings)} vulnerabilities", file=sys.stderr)
            
        except Exception as e:
            print(f"[!] POST error: {e}", file=sys.stderr)
        
        return findings

    def group_findings(self, findings):
        grouped = defaultdict(lambda: {
            'url': '',
            'method': '',
            'template': '',
            'severity': '',
            'params_found': set(),
            'reflected_payloads': set(),
            'sample_urls': []
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
        # لود کردن لیست پارامترها و payloadها
        params = self.load_file('top29-xss.txt')
        payloads = self.load_file('payloads.txt')

        if not params:
            params = ['q', 's', 'search', 'id', 'page', 'view', 'action']
        if not payloads:
            payloads = ['mamad', '"mamad"', "'mamad'"]

        # خوندن URLهای معتبر از valid_urls.txt
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

        # نمایش نمونه URLهای معتبر
        print("\n[*] Sample validated URLs:", file=sys.stderr)
        for url in url_list[:5]:
            print(f"  {url}", file=sys.stderr)
        if len(url_list) > 5:
            print(f"  ... and {len(url_list) - 5} more", file=sys.stderr)

        # تولید URLهای GET از URLهای معتبر
        print("\n[*] Generating GET URLs from validated URLs...", file=sys.stderr)
        get_urls = self.generate_get_urls_from_list(url_list, params, payloads)
        
        with open(self.get_urls_file, 'w') as f:
            f.write('\n'.join(get_urls))
        print(f"[+] Generated {len(get_urls)} GET URLs", file=sys.stderr)
        print(f"[+] Saved to: {self.get_urls_file}", file=sys.stderr)

        # ذخیره POST URLها
        post_urls = [url for url in url_list if not parse_qs(urlparse(url).query)]
        if not post_urls:
            post_urls = [target_url]
        
        with open(self.post_urls_file, 'w') as f:
            f.write('\n'.join(post_urls))
        print(f"[+] Saved {len(post_urls)} POST URLs", file=sys.stderr)

        # نمایش نمونه URLهای تولید شده
        print("\n[*] Sample generated GET URLs:", file=sys.stderr)
        for url in get_urls[:5]:
            print(f"  {unquote(url)[:120]}", file=sys.stderr)
        if len(get_urls) > 5:
            print(f"  ... and {len(get_urls) - 5} more", file=sys.stderr)

        # اجرای Nuclei
        print("\n" + "-"*70, file=sys.stderr)
        get_findings = self.run_nuclei_get(payloads)
        
        print("-"*70, file=sys.stderr)
        post_findings = self.run_nuclei_post(payloads)

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
    
    # اگه فایل custom داده شده
    if args.urls_file:
        x9.valid_urls_file = Path(args.urls_file)
    
    x9.run(args.url)


if __name__ == '__main__':
    main()
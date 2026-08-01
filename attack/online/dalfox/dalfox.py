#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vajra Dalfox XSS Scanner – strictly pivots from X9 results.
Only runs when X9 has identified vulnerable parameters.
"""

import sys
import json
import subprocess
import os
import time
import shutil
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse
from collections import defaultdict

# ----------- CONFIGURATION -----------
WORKERS = 50
TIMEOUT = 10
DELAY_MS = 0
WAF_EVASION = False
# -------------------------------------

class DalfoxIntegrator:
    def __init__(self, target_url):
        parsed = urlparse(target_url if target_url.startswith("http") else f"https://{target_url}")
        self.domain = parsed.netloc
        self.target_url = target_url if target_url.startswith("http") else f"https://{target_url}"

        self.base_dir = Path(__file__).parent.resolve()
        self.vajra_root = self.base_dir.parent.parent.parent
        self.target_dir = self.vajra_root / "targets" / self.domain
        self.x9_dir = self.target_dir / "attack" / "online" / "x9"
        self.output_dir = self.target_dir / "attack" / "online" / "dalfox"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.x9_result_file = self.x9_dir / "result.json"
        self.url_list_file = self.output_dir / "dalfox_urls.txt"
        self.result_file = self.output_dir / "dalfox_result.json"

        self.debug = False

    def check_dalfox(self):
        if shutil.which("dalfox") is None:
            print("❌ Dalfox is not installed or not in PATH.")
            return False
        return True

    def load_x9_findings(self):
        """Returns list of findings if X9 result.json exists and contains findings, else []."""
        if not self.x9_result_file.exists():
            print(f"[!] X9 result not found: {self.x9_result_file}")
            return []
        try:
            with open(self.x9_result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            findings = data.get('findings', [])
            if not findings:
                print("[!] X9 result contains no vulnerable endpoints.")
            return findings
        except Exception as e:
            print(f"[!] Error reading X9 result: {e}")
            return []

    def build_urls_from_findings(self, findings):
        """Build one URL per endpoint containing all vulnerable params with test value."""
        endpoint_params = defaultdict(set)
        for f in findings:
            base_url = f.get('url')
            if not base_url:
                continue
            parsed = urlparse(base_url)
            clean_base = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
            for param in f.get('vulnerable_params', []):
                endpoint_params[clean_base].add(param)

        urls = []
        for base, params in endpoint_params.items():
            sorted_params = sorted(params)
            query = urlencode({p: 'dalfoxtest' for p in sorted_params})
            full_url = urlunparse(urlparse(base)._replace(query=query))
            urls.append(full_url)
        return urls

    def write_url_list(self, urls):
        with open(self.url_list_file, 'w') as f:
            f.write('\n'.join(urls))
        return self.url_list_file

    def run_dalfox(self, skip_mining=True):
        # Remove previous result to avoid append
        if self.result_file.exists():
            self.result_file.unlink()

        cmd = [
            "dalfox", "file", str(self.url_list_file),
            "--worker", str(WORKERS),
            "--timeout", str(TIMEOUT),
            "--format", "json",
            "--output", str(self.result_file),
            "--silence",
            "--no-spinner",
            "--no-color",
            "--follow-redirects",
        ]
        if skip_mining:
            cmd.append("--skip-mining-all")
        if WAF_EVASION:
            cmd.append("--waf-evasion")
        if DELAY_MS:
            cmd += ["--delay", str(DELAY_MS)]

        if self.debug:
            print(f"[DEBUG] CMD: {' '.join(cmd)}", file=sys.stderr)

        print(f"\n🚀 Running Dalfox on {len(open(self.url_list_file).readlines())} URL(s)...\n")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0 and proc.stderr:
                print(f"[!] Dalfox error: {proc.stderr}", file=sys.stderr)
            return proc.returncode == 0
        except FileNotFoundError:
            print("❌ Dalfox command not found.")
            return False

    def parse_results(self):
        if not self.result_file.exists():
            return [], {}, []

        try:
            with open(self.result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                return [], {}, []
        except Exception:
            return [], {}, []

        findings = []
        http_stats = defaultdict(int)
        all_params = set()

        for item in data:
            if not item:
                continue
            findings.append(item)
            if 'param' in item:
                all_params.add(item['param'])

        return findings, dict(http_stats), sorted(all_params)

    def print_summary(self, findings, http_stats, vuln_params, scan_time):
        total = len(findings)
        verified = sum(1 for f in findings if f.get('type') == 'V')
        reflected = sum(1 for f in findings if f.get('type') == 'R')

        unique_hosts = set()
        for f in findings:
            url = f.get('data', '')
            if url:
                host = urlparse(url).netloc
                if host:
                    unique_hosts.add(host)

        print("\n" + "="*60)
        print(" ⚔️  VAJRA + Dalfox XSS Scan Results")
        print("="*60)
        print(f" 🎯 Domain          : {self.domain}")
        print(f" ⏱️  Scan duration   : {scan_time:.1f}s")
        print("-"*60)

        if not findings:
            print(" [✓] No XSS vulnerabilities found.")
        else:
            print(f" 🔥 XSS FOUND!  Total PoCs: {total}")
            print(f"     ├─ Verified   : {verified}")
            print(f"     └─ Reflected  : {reflected}")
            if vuln_params:
                print(f"     🔍 Vulnerable Params : {', '.join(vuln_params)}")
            print("-"*60)
            print(" 🌐 Vulnerable endpoints (base URLs):")
            for host in sorted(unique_hosts):
                print(f"     • {host}")
            print("-"*60)
            print(" ℹ️  Full PoC URLs (with payload) are saved in:")
            print(f"     {self.result_file}")
        print("="*60)

    def run(self):
        start_time = time.time()

        if not self.check_dalfox():
            return

        # Strictly require X9 findings
        x9_findings = self.load_x9_findings()
        if not x9_findings:
            print("[!] No X9 vulnerable parameters found. Dalfox skipped (requires prior X9 results).")
            return

        print(f"[+] Loaded {len(x9_findings)} vulnerable endpoints from X9.")
        urls = self.build_urls_from_findings(x9_findings)

        if not urls:
            print("[-] Could not build any URLs. Exiting.")
            return

        print(f"[+] Prepared {len(urls)} URL(s) for Dalfox.")
        self.write_url_list(urls)

        success = self.run_dalfox(skip_mining=True)
        if not success:
            print("[!] Dalfox scan did not complete successfully.")
            return

        findings, http_stats, vuln_params = self.parse_results()
        elapsed = time.time() - start_time
        self.print_summary(findings, http_stats, vuln_params, elapsed)

        # Keep the URL file for reference if needed (cleanup optional)
        # if self.url_list_file.exists():
        #     self.url_list_file.unlink()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dalfox XSS Scanner (Vajra integration)")
    parser.add_argument("target", help="Target URL (e.g., https://example.com)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    runner = DalfoxIntegrator(args.target)
    runner.debug = args.debug
    runner.run()


if __name__ == "__main__":
    main()

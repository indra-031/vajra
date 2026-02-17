#!/usr/bin/env python3

import os
import sys
import subprocess
import json
from urllib.parse import urlparse

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc

def run_retire(scan_path: str, output_path: str):
    # print(f"\n[+] Scanning: {scan_path}")

    result = subprocess.run(
        [
            "retire",
            "--path", scan_path,
            "--outputformat", "json",
            "--outputpath", output_path
        ]
    )

    # print(f"[✓] Finished scanning: {scan_path}")
    # print(f"[DEBUG] Exit code: {result.returncode}")

def parse_summary(json_path, severity_counter):
    if not os.path.isfile(json_path):
        return 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return 0

    count = 0

    for item in data.get("data", []):
        for result in item.get("results", []):
            for vuln in result.get("vulnerabilities", []):
                sev = (vuln.get("severity") or "unknown").lower()
                severity_counter[sev] = severity_counter.get(sev, 0) + 1
                count += 1

    return count

def main():
    if len(sys.argv) != 2:
        print("Usage: retirejs.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])
    base = "../../targets"

    js_dir = f"{base}/{domain}/download/js"
    inline_dir = f"{base}/{domain}/download/inline-js"
    html_dir = f"{base}/{domain}/download/html"

    out_dir = f"{base}/{domain}/attack/offline/retire"
    os.makedirs(out_dir, exist_ok=True)

    print("[+] Running retire.js static scan")

    if os.path.isdir(js_dir):
        run_retire(js_dir, f"{out_dir}/js.json")
    else:
        print("[-] JS directory not found")

    if os.path.isdir(inline_dir):
        run_retire(inline_dir, f"{out_dir}/inline-js.json")
    else:
        print("[-] inline-js directory not found")

    if os.path.isdir(html_dir):
        run_retire(html_dir, f"{out_dir}/html.json")
    else:
        print("[-] HTML directory not found")

    # print("\n[✓] All scans completed")

    # -------- SUMMARY --------
    severity_counter = {}
    total = 0

    for file in ["js.json", "inline-js.json", "html.json"]:
        total += parse_summary(f"{out_dir}/{file}", severity_counter)

    # print("\n========== SUMMARY ==========")

    if total == 0:
        print("No vulnerabilities found ✅")
    else:
        print(f"Total vulnerabilities found: {total}")
        for sev, count in severity_counter.items():
            print(f"{sev.capitalize()} : {count}")

    # print("=============================\n")

if __name__ == "__main__":
    main()

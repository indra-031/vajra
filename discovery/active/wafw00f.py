#!/usr/bin/env python3
# discovery/active/waf.py
# Detect WAF using wafw00f
# Output goes to targets/<domain>/result/waf.txt

import os
import sys
import subprocess
from urllib.parse import urlparse


def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_wafw00f(target: str) -> str:
    try:
        return subprocess.check_output(
            ["wafw00f", target],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except Exception:
        return ""


def parse_waf_result(output: str) -> str:
    for line in output.splitlines():
        if "[+]" in line and "behind" in line.lower():
            return line.strip()
    if "No WAF detected" in output:
        return "WAF not detected"
    return "WAF detection inconclusive"


def save_result(domain: str, data: str):
    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    out_dir = os.path.join(base_targets, domain, "waf")
    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, "waf.txt")
    with open(out_file, "w") as f:
        f.write(data.strip() + "\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: waf.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    raw_output = run_wafw00f(target)
    parsed_result = parse_waf_result(raw_output)

    save_result(domain, raw_output)

    if parsed_result == "WAF not detected":
        print("[-] WAF not detected")
    else:
        print(f"{parsed_result}")


if __name__ == "__main__":
    main()

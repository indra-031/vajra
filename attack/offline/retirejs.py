#!/usr/bin/env python3

import os
import sys
import subprocess
import json
from urllib.parse import urlparse


# ----------------------------
# Helpers
# ----------------------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def get_project_root() -> str:
    """
    Resolve project root dynamically based on this file location.
    attack/offline/retirejs.py  ->  ../../ (project root)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "../../"))


def run_retire(scan_path: str, output_path: str):
    result = subprocess.run(
        [
            "retire",
            "--path", scan_path,
            "--outputformat", "json",
            "--outputpath", output_path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode


def parse_summary(json_path, severity_counter):
    if not os.path.isfile(json_path):
        return 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return 0

    count = 0

    for item in data.get("data", []):
        for result in item.get("results", []):
            for vuln in result.get("vulnerabilities", []):
                sev = (vuln.get("severity") or "unknown").lower()
                severity_counter[sev] = severity_counter.get(sev, 0) + 1
                count += 1

    return count


# ----------------------------
# Main
# ----------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: retirejs.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])
    project_root = get_project_root()

    base = os.path.join(project_root, "targets")

    js_dir = os.path.join(base, domain, "download", "js")
    inline_dir = os.path.join(base, domain, "download", "inline-js")
    html_dir = os.path.join(base, domain, "download", "html")

    out_dir = os.path.join(base, domain, "attack", "offline", "retire")
    os.makedirs(out_dir, exist_ok=True)

    print("[+] Running retire.js static scan")

    if os.path.isdir(js_dir):
        run_retire(js_dir, os.path.join(out_dir, "js.json"))
    else:
        print("[-] JS directory not found")

    if os.path.isdir(inline_dir):
        run_retire(inline_dir, os.path.join(out_dir, "inline-js.json"))
    else:
        print("[-] inline-js directory not found")

    if os.path.isdir(html_dir):
        run_retire(html_dir, os.path.join(out_dir, "html.json"))
    else:
        print("[-] HTML directory not found")

    # -------- SUMMARY --------
    severity_counter = {}
    total = 0

    for file in ["js.json", "inline-js.json", "html.json"]:
        total += parse_summary(os.path.join(out_dir, file), severity_counter)

    if total == 0:
        print("No vulnerabilities found ✅")
    else:
        print(f"Total vulnerabilities found: {total}")
        for sev in sorted(severity_counter):
            print(f"{sev.capitalize()} : {severity_counter[sev]}")


if __name__ == "__main__":
    main()

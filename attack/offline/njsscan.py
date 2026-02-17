#!/usr/bin/env python3
# analysis/vuln-scan/njsscan.py
# Static JS Scan (njsscan)
# Reads from :
#   targets/<DOMAIN>/download/js
#   targets/<DOMAIN>/download/inline-js
#   targets/<DOMAIN>/download/html
# Writes to :
#   targets/<DOMAIN>/attack/offline/njsscan/

import os
import sys
import json
import subprocess
import tempfile
from urllib.parse import urlparse

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc

def collect_scan_dirs(base_dir: str):
    candidates = [
        os.path.join(base_dir, "download", "js"),
        os.path.join(base_dir, "download", "inline-js"),
        os.path.join(base_dir, "download", "html"),
    ]
    return [d for d in candidates if os.path.isdir(d)]

def run_njsscan(scan_dirs, output_file: str):
    cmd = [
        "njsscan",
        "--json",
        "-o", output_file,
    ]

    for d in scan_dirs:
        cmd.append(d)

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def parse_results(njsscan_json: str):
    if not os.path.isfile(njsscan_json):
        return {}, []

    try:
        with open(njsscan_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}, []

    nodejs_issues = data.get("nodejs", {})

    summary = {
        "total_issues": 0,
        "by_rule": {},
        "severity": {
            "error": 0,
            "warning": 0,
            "info": 0
        }
    }

    findings = []

    for rule, content in nodejs_issues.items():
        files = content.get("files", [])
        metadata = content.get("metadata", {})
        severity = metadata.get("severity", "INFO").lower()

        if not files:
            continue

        count = len(files)
        summary["total_issues"] += count

        summary["by_rule"][rule] = {
            "count": count,
            "severity": severity,
            "cwe": metadata.get("cwe"),
            "description": metadata.get("description")
        }

        if severity in summary["severity"]:
            summary["severity"][severity] += count
        else:
            summary["severity"][severity] = count

        for f in files:
            findings.append({
                "rule": rule,
                "file": f.get("file"),
                "line": f.get("line"),
                "severity": severity,
                "cwe": metadata.get("cwe"),
                "description": metadata.get("description")
            })

    return summary, findings

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: njsscan.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    target_dir = os.path.join(base_targets, domain)

    scan_dirs = collect_scan_dirs(target_dir)

    if not scan_dirs:
        print("[!] No JS / inline-js / html directories found")
        sys.exit(0)

    print("[+] Running njsscan")

    with tempfile.TemporaryDirectory() as tmpdir:

        tmp_output = os.path.join(tmpdir, "njsscan.json")

        run_njsscan(scan_dirs, tmp_output)

        summary, findings = parse_results(tmp_output)

        if not findings:
            print("[!] No issues found")
            return

        # ---------- Output ----------
        out_dir = os.path.join(
            base_targets,
            domain,
            "attack",
            "offline",
            "njsscan"
        )

        os.makedirs(out_dir, exist_ok=True)

        raw_output = os.path.join(out_dir, "njsscan.json")
        summary_file = os.path.join(out_dir, "summary.json")
        findings_file = os.path.join(out_dir, "findings.json")

        # ذخیره خروجی خام
        run_njsscan(scan_dirs, raw_output)

        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        with open(findings_file, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2)

        # print("\n[✓] DONE")
        # print(f" Path : targets/{domain}/attack/offline/njsscan/")
        print(f" Total issues : {summary['total_issues']}")
        # print(f" Errors : {summary['severity'].get('error', 0)} | "
            #   f" Warnings : {summary['severity'].get('warning', 0)}")

if __name__ == "__main__":
    main()

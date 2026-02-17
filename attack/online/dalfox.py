#!/usr/bin/env python3
# attack/online/dalfox.py
# Advanced Dalfox Integration with ETA + HTTP Stats + Live Output

import os
import sys
import subprocess
import tempfile
import json
import time
from urllib.parse import urlparse

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def count_lines(file_path: str) -> int:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def parse_results(json_file: str):
    stats = {}
    findings = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}, []

    for item in data:
        findings.append(item)
        status = str(item.get("status", "unknown"))
        stats[status] = stats.get(status, 0) + 1

    return stats, findings


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: dalfox.py <target>")
        sys.exit(1)

    start_time = time.time()

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    target_base = os.path.join(base_targets, domain)

    input_file = os.path.join(
        target_base,
        "extraction",
        "merge",
        "urls-with-param.txt"
    )

    if not os.path.isfile(input_file):
        print("[!] urls-with-param.txt not found")
        sys.exit(1)

    total_targets = count_lines(input_file)

    if total_targets == 0:
        print("[!] No URLs to scan")
        sys.exit(0)

    print("=" * 60)
    print(" Vajra Online Attack Phase - Dalfox")
    print("=" * 60)
    print(f" Target Domain : {domain}")
    print(f" Total URLs    : {total_targets}")
    print(" Workers       : 5")
    print(" Mode          : file")
    print("-" * 60)

    # تخمین زمان تقریبی
    estimated_seconds = total_targets * 1.5
    print(f" Estimated time: ~{int(estimated_seconds)} seconds\n")

    # خروجی موقت
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_output = tmp.name

    cmd = [
        "dalfox",
        "file",
        input_file,
        "--format", "json",
        "--output", temp_output,
        "--worker", "5",
        "--timeout", "10",
        "--follow-redirects",
        "--skip-mining-all",
        "--no-color"
    ]

    # اجرای زنده (انگار خودت ران کردی)
    process = subprocess.Popen(cmd)

    process.wait()

    elapsed = int(time.time() - start_time)

    stats, findings = parse_results(temp_output)

    print("\n" + "=" * 60)
    print(" Scan Finished")
    print("=" * 60)
    print(f" Elapsed Time : {elapsed} seconds")

    if not findings:
        os.remove(temp_output)
        print("\n[✓] No XSS vulnerabilities found")
        sys.exit(0)

    # اگر finding داشت → ذخیره کن
    out_dir = os.path.join(
        target_base,
        "attack",
        "online",
        "dalfox"
    )
    os.makedirs(out_dir, exist_ok=True)

    final_output = os.path.join(out_dir, "dalfox.json")
    os.replace(temp_output, final_output)

    print(f"\n[🔥] XSS FOUND! ({len(findings)} findings)")
    print("\n HTTP Status Breakdown:")

    for code, count in sorted(stats.items()):
        print(f"  ├─ {code}: {count}")

    print("\n Saved to:")
    print(f" targets/{domain}/attack/online/dalfox/dalfox.json")
    print("=" * 60)


if __name__ == "__main__":
    main()

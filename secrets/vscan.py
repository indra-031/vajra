#!/usr/bin/env python3
# secret/vscan.py
# Vajra Native Secret Scanner (JSON)

import sys
import re
import json
from pathlib import Path
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def build_targets_base() -> Path:
    return Path(__file__).resolve().parents[1] / "targets"


def collect_files(directory: Path):
    if not directory.exists():
        return []

    return [
        f for f in directory.rglob("*")
        if f.suffix.lower() in (".js", ".html")
    ]


# ---------------- PATTERNS ----------------

PATTERNS = {
    "Username": re.compile(
        r'(?i)\b(user(name)?|login)\b\s*[:=]\s*[\'"]([^\'"]+)[\'"]'
    ),

    "Password": re.compile(
        r'(?i)\b(password|passwd|pwd)\b\s*[:=]\s*[\'"]([^\'"]+)[\'"]'
    ),

    "API Key": re.compile(
        r'(?i)\b(api[_-]?key|apikey)\b\s*[:=]\s*[\'"]([^\'"]+)[\'"]'
    ),

    "AWS Access Key": re.compile(
        r'\bAKIA[0-9A-Z]{16}\b'
    ),

    "Slack Webhook": re.compile(
        r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+'
    ),

    "JWT": re.compile(
        r'\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b'
    ),
}


# ---------------- SCANNER ----------------

def scan_file(path: Path, base_path: Path):
    findings = []

    try:
        lines = path.read_text(errors="ignore").splitlines()
    except Exception:
        return findings

    for lineno, line in enumerate(lines, start=1):
        for name, regex in PATTERNS.items():
            for match in regex.finditer(line):

                value = match.group(0)

                findings.append({
                    "file": str(path.relative_to(base_path)),
                    "type": name,
                    "match": value,
                    "line_number": lineno,
                    "line_content": line.strip()
                })

    return findings


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: vscan.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])
    base_targets = build_targets_base()
    target_dir = base_targets / domain

    js_dir = target_dir / "download" / "js"
    html_dir = target_dir / "download" / "html"
    inline_dir = target_dir / "download" / "inline-js"

    if not any(d.exists() for d in (js_dir, html_dir, inline_dir)):
        print("[!] No JS / HTML / inline-js directories found")
        sys.exit(1)

    print("[+] Running Vajra Scan (vscan)")

    all_findings = []
    seen = set()

    for scan_dir in (js_dir, inline_dir, html_dir):
        if not scan_dir.exists():
            continue

        # print(f" ├─ Scanning {scan_dir.name}")

        for file in collect_files(scan_dir):
            results = scan_file(file, target_dir)

            for item in results:
                fingerprint = (
                    item["file"],
                    item["line_number"],
                    item["match"]
                )

                if fingerprint not in seen:
                    seen.add(fingerprint)
                    all_findings.append(item)

    if not all_findings:
        # print("[!] No secrets found")
        return

    out_dir = target_dir / "secret" / "vscan"
    out_dir.mkdir(parents=True, exist_ok=True)

    output_file = out_dir / "vscan.json"

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(all_findings, f, indent=4)

    # print("\n[✓] DONE")
    # print(f" Path : targets/{domain}/secret/vscan/vscan.json")


if __name__ == "__main__":
    main()

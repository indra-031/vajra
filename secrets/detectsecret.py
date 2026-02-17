#!/usr/bin/env python3
# secret/detect_secrets.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_detect_secrets(scan_dir: str, out_file: str) -> bool:
    cmd = [
        "detect-secrets",
        "scan",
        "-C", scan_dir,
        "--cores", "1"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    output = result.stdout.strip()

    # اگر خروجی تقریباً خالی بود → چیزی پیدا نشده
    if len(output) <= 2:
        return False

    # فقط وقتی پیدا شد ذخیره کن
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output)

    return True


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: detect_secrets.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")
    html_dir = os.path.join(base_targets, domain, "download", "html")
    inline_js_dir = os.path.join(base_targets, domain, "download", "inline-js")

    if not any(os.path.isdir(d) for d in (js_dir, html_dir, inline_js_dir)):
        print("[!] No JS / HTML / inline-js directories found")
        sys.exit(1)

    out_dir = os.path.join(
        base_targets,
        domain,
        "secret",
        "detect-secrets"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running detect-secrets")

    if os.path.isdir(js_dir):
        # print(" ├─ Scanning JS")
        js_out = os.path.join(out_dir, "js.json")
        if run_detect_secrets(js_dir, js_out):
            found = True

    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline JS")
        inline_out = os.path.join(out_dir, "inline-js.json")
        if run_detect_secrets(inline_js_dir, inline_out):
            found = True

    if os.path.isdir(html_dir):
        # print(" ├─ Scanning HTML")
        html_out = os.path.join(out_dir, "html.json")
        if run_detect_secrets(html_dir, html_out):
            found = True

    if not found:
        # حذف پوشه اگر خالی بود
        try:
            os.rmdir(out_dir)
        except:
            pass

        # print("[!] No secrets found")
    else:
        pass
        # print("\n[✓] DONE")
        # print(f" Path : targets/{domain}/secret/detect-secrets/")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# secret/gitleaks.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_gitleaks(scan_dir: str, out_file: str) -> bool:
    cmd = [
        "gitleaks",
        "detect",
        "--source", scan_dir,
        "--report-format", "json",
        "--report-path", out_file,
        "--no-banner",
        "--redact",
        "--exit-code", "0",
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )

    # اگر فایل meaningful بود
    if os.path.exists(out_file) and os.path.getsize(out_file) > 5:
        return True

    # اگر چیزی پیدا نشد → فایل حذف شود
    if os.path.exists(out_file):
        os.remove(out_file)

    return False


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: gitleaks.py <domain>")
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
        "gitleaks"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running Gitleaks")

    if os.path.isdir(js_dir):
        # print(" ├─ Scanning JS")
        js_out = os.path.join(out_dir, "js.json")
        if run_gitleaks(js_dir, js_out):
            found = True

    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline JS")
        inline_out = os.path.join(out_dir, "inline-js.json")
        if run_gitleaks(inline_js_dir, inline_out):
            found = True

    if os.path.isdir(html_dir):
        # print(" ├─ Scanning HTML")
        html_out = os.path.join(out_dir, "html.json")
        if run_gitleaks(html_dir, html_out):
            found = True

    if not found:
        # اگر هیچ خروجی نداشت → پوشه حذف شود
        try:
            os.rmdir(out_dir)
        except:
            pass

        # print("[!] No secrets found")
    else:
        pass
        # print("\n[✓] DONE")
        # print(f" Path : targets/{domain}/secret/gitleaks/")


if __name__ == "__main__":
    main()

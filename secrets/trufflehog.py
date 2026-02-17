#!/usr/bin/env python3
# secret/trufflehog.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_trufflehog(scan_dir: str) -> str:
    cmd = [
        "trufflehog",
        "filesystem",
        scan_dir,
        "--json",
        "--no-update",
        "--no-verification",
        "--filter-entropy=0",
        "--results=all"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.stdout.strip()


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: trufflehog.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    target_dir = os.path.join(project_root, "targets", domain)

    js_dir = os.path.join(target_dir, "download", "js")
    inline_js_dir = os.path.join(target_dir, "download", "inline-js")
    html_dir = os.path.join(target_dir, "download", "html")

    if not any(os.path.isdir(d) for d in (js_dir, inline_js_dir, html_dir)):
        print("[!] No JS / HTML / inline-js directories found")
        sys.exit(1)

    out_dir = os.path.join(
        target_dir,
        "secret",
        "trufflehog"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running TruffleHog")

    # ---------- JS ----------
    if os.path.isdir(js_dir):
        # print(" ├─ Scanning JS")
        output = run_trufflehog(js_dir)
        if output:
            with open(os.path.join(out_dir, "js.json"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- inline-js ----------
    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline-js")
        output = run_trufflehog(inline_js_dir)
        if output:
            with open(os.path.join(out_dir, "inline-js.json"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- HTML ----------
    if os.path.isdir(html_dir):
        # print(" ├─ Scanning HTML")
        output = run_trufflehog(html_dir)
        if output:
            with open(os.path.join(out_dir, "html.json"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    if not found:
        try:
            os.rmdir(out_dir)
        except:
            pass

        # print("[!] No secrets found")
    else:
        pass
        # print("\n[✓] DONE")
        # print(f" Path : targets/{domain}/secret/trufflehog/")


if __name__ == "__main__":
    main()

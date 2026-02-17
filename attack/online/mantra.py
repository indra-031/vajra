#!/usr/bin/env python3
# secret/mantra.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_mantra(scan_dir: str) -> str:
    cmd = [
        "mantra",
        "-s",          # silent
        "-d",          # detailed
        "-t", "50",    # threads
        scan_dir
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
        print("Usage: mantra.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")
    inline_js_dir = os.path.join(base_targets, domain, "download", "inline-js")
    html_dir = os.path.join(base_targets, domain, "download", "html")

    if not any(os.path.isdir(d) for d in (js_dir, inline_js_dir, html_dir)):
        print("[!] No JS / HTML / inline-js directories found")
        sys.exit(1)

    out_dir = os.path.join(
        base_targets,
        domain,
        "secret",
        "mantra"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running Mantra")

    # ---------- JS ----------
    if os.path.isdir(js_dir):
        print(" ├─ Scanning JS")
        output = run_mantra(js_dir)
        if output:
            with open(os.path.join(out_dir, "js.txt"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- inline-js ----------
    if os.path.isdir(inline_js_dir):
        print(" ├─ Scanning inline-js")
        output = run_mantra(inline_js_dir)
        if output:
            with open(os.path.join(out_dir, "inline-js.txt"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- HTML ----------
    if os.path.isdir(html_dir):
        print(" ├─ Scanning HTML")
        output = run_mantra(html_dir)
        if output:
            with open(os.path.join(out_dir, "html.txt"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    if not found:
        try:
            os.rmdir(out_dir)
        except:
            pass

        print("[!] No secrets found")
    else:
        print("\n[✓] DONE")
        print(f" Path : targets/{domain}/secret/mantra/")


if __name__ == "__main__":
    main()

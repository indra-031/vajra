#!/usr/bin/env python3
# secret/secretfinder.py

import os
import sys
import subprocess
from urllib.parse import urlparse
from pathlib import Path

# ------------- CONFIG -------------

BASE_DIR = Path(__file__).resolve().parent
SECRETFINDER_PATH = (
    BASE_DIR / "../.tools/SecretFinder/SecretFinder.py"
).resolve()

PYTHON_BIN = "python3"

# ------------- HELPERS -------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_secretfinder(scan_dir: str) -> str:
    cmd = [
        PYTHON_BIN,
        str(SECRETFINDER_PATH),
        "-i", scan_dir,
        "-o", "/dev/stdout"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.stdout.strip()


# ------------- MAIN -------------

def main():
    if len(sys.argv) != 2:
        print("Usage: secretfinder.py <domain>")
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
        "secretfinder"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running SecretFinder")

    # ---------- JS ----------
    if os.path.isdir(js_dir):
        output = run_secretfinder(js_dir)
        if output:
            with open(os.path.join(out_dir, "js.html"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- inline-js ----------
    if os.path.isdir(inline_js_dir):
        output = run_secretfinder(inline_js_dir)
        if output:
            with open(os.path.join(out_dir, "inline-js.html"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- HTML ----------
    if os.path.isdir(html_dir):
        output = run_secretfinder(html_dir)
        if output:
            with open(os.path.join(out_dir, "html.html"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    if not found:
        try:
            os.rmdir(out_dir)
        except:
            pass


if __name__ == "__main__":
    main()

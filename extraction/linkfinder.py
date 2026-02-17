#!/usr/bin/env python3
# extraction/linkfinder/linkfinder.py

import os
import sys
import subprocess
from urllib.parse import urlparse
from pathlib import Path

# ---------------- CONFIG ----------------

BASE_DIR = Path(__file__).resolve().parent
LINKFINDER_BIN = (
    BASE_DIR / "../.tools/LinkFinder/linkfinder.py"
).resolve()

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_linkfinder(input_path: str, html_output: str):
    subprocess.run(
        [
            sys.executable,
            str(LINKFINDER_BIN),
            "-i", input_path,
            "-o", html_output
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def scan_directory(directory: str, html_output: str, label: str):
    # print(f" ├─ Scanning {label}")
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith((".js", ".html", ".htm")):
                full_path = os.path.join(root, filename)
                run_linkfinder(full_path, html_output)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: linkfinder.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

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
        "extraction",
        "linkfinder"
    )

    os.makedirs(out_dir, exist_ok=True)

    html_output = os.path.join(out_dir, "output.html")

    # reset output file
    open(html_output, "w").close()

    print("[+] Running LinkFinder")

    if os.path.isdir(js_dir):
        scan_directory(js_dir, html_output, "JS files")

    if os.path.isdir(inline_js_dir):
        scan_directory(inline_js_dir, html_output, "inline JS files")

    if os.path.isdir(html_dir):
        scan_directory(html_dir, html_output, "HTML files")


if __name__ == "__main__":
    main()

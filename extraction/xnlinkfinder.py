#!/usr/bin/env python3
# extraction/xnlinkfinder/xnlinkfinder.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_xnlinkfinder(input_dir: str, out_dir: str, config_file: str | None):
    cmd = [
        "xnLinkFinder",
        "-i", input_dir,
        "-o", os.path.join(out_dir, "links.txt"),
        "-op", os.path.join(out_dir, "parameters.txt"),
        "-os", os.path.join(out_dir, "secrets.txt"),
        "-oo", os.path.join(out_dir, "out_of_scope.txt"),
        "-owl", os.path.join(out_dir, "wordlist.txt"),
        "-nb"
    ]

    if config_file and os.path.isfile(config_file):
        cmd += ["--config", config_file]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def count_lines(path: str) -> int:
    try:
        with open(path, "r", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: xnlinkfinder.py <target>")
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
        "xnlinkfinder"
    )

    os.makedirs(out_dir, exist_ok=True)

    # فایل‌های خروجی
    output_files = [
        "links.txt",
        "parameters.txt",
        "secrets.txt",
        "out_of_scope.txt",
        "wordlist.txt"
    ]

    # reset outputs
    for filename in output_files:
        open(os.path.join(out_dir, filename), "w").close()

    config_file = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../configs/xnLinkFinder/config.yml"
        )
    )

    print("[+] Running xnLinkFinder")

    if os.path.isdir(js_dir):
        # print(" ├─ Scanning JS files")
        run_xnlinkfinder(js_dir, out_dir, None)

    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline JS files")
        run_xnlinkfinder(inline_js_dir, out_dir, None)

    if os.path.isdir(html_dir):
        # print(" ├─ Scanning HTML files")
        run_xnlinkfinder(html_dir, out_dir, None)

    total_links = count_lines(os.path.join(out_dir, "links.txt"))
    total_params = count_lines(os.path.join(out_dir, "parameters.txt"))
    total_secrets = count_lines(os.path.join(out_dir, "secrets.txt"))

    # print("\n[✓] DONE")
    print(f" Links      : {total_links}")
    print(f" Parameters : {total_params}")
    print(f" Secrets    : {total_secrets}")
    # print(f" Path : targets/{domain}/extraction/xnlinkfinder/")


if __name__ == "__main__":
    main()

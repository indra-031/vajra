#!/usr/bin/env python3
# secret/dumpsterdiver.py

import os
import sys
import subprocess
from urllib.parse import urlparse
from pathlib import Path

# ------------- CONFIG -------------

BASE_DIR = Path(__file__).resolve().parent
DUMPSTERDIVER_PATH = (
    BASE_DIR / "../.tools/DumpsterDiver/DumpsterDiver.py"
).resolve()

PYTHON_BIN = "python3"

DD_FLAGS = [
    "-a",
    "-s"
]

# ------------- HELPERS -------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_dumpsterdiver(input_dir: str, output_file: str) -> bool:
    cmd = [
        PYTHON_BIN,
        str(DUMPSTERDIVER_PATH),
        "-p", input_dir,
        "-o", output_file,
        *DD_FLAGS
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )

    # اگر فایل ساخته شد و meaningful بود
    if os.path.exists(output_file) and os.path.getsize(output_file) > 50:
        return True

    # اگر چیزی پیدا نشد → فایل حذف شود
    if os.path.exists(output_file):
        os.remove(output_file)

    return False


# ------------- MAIN -------------

def main():
    if len(sys.argv) != 2:
        print("Usage: dumpsterdiver.py <domain>")
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
        "dumpsterdiver"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running DumpsterDiver")

    if os.path.isdir(js_dir):
        js_out = os.path.join(out_dir, "js.json")
        if run_dumpsterdiver(js_dir, js_out):
            found = True

    if os.path.isdir(inline_js_dir):
        inline_out = os.path.join(out_dir, "inline-js.json")
        if run_dumpsterdiver(inline_js_dir, inline_out):
            found = True

    if os.path.isdir(html_dir):
        html_out = os.path.join(out_dir, "html.json")
        if run_dumpsterdiver(html_dir, html_out):
            found = True

    if not found:
        try:
            os.rmdir(out_dir)
        except:
            pass


if __name__ == "__main__":
    main()

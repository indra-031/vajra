#!/usr/bin/env python3
# analysis/extract_inline_js.py

import os
import sys
import hashlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def hash_content(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


# ---------------- CORE ----------------

def extract_inline_js(html_dir: str, js_output_dir: str, map_file: str) -> int:
    os.makedirs(js_output_dir, exist_ok=True)

    total_scripts = 0

    for filename in os.listdir(html_dir):
        if not filename.lower().endswith((".html", ".htm")):
            continue

        html_path = os.path.join(html_dir, filename)

        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, "html.parser")

        scripts = soup.find_all("script")

        for script in scripts:
            # skip external scripts
            if script.get("src"):
                continue

            code = script.string
            if not code or not code.strip():
                continue

            code = code.strip()
            file_hash = hash_content(code)

            js_filename = f"{file_hash}.js"
            js_path = os.path.join(js_output_dir, js_filename)

            # avoid duplicates (content-based)
            if not os.path.exists(js_path):
                with open(js_path, "w", encoding="utf-8") as out:
                    out.write(code)

            # write to central hash-map
            with open(map_file, "a") as m:
                m.write(f"{file_hash} {filename}\n")

            total_scripts += 1

    return total_scripts


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: extract_inline_js.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    html_dir = os.path.join(base_targets, domain, "download", "html")
    js_output_dir = os.path.join(base_targets, domain, "download", "inline-js")
    hash_dir = os.path.join(base_targets, domain, "download", "hash-map")

    if not os.path.isdir(html_dir):
        print("[!] HTML directory not found")
        sys.exit(1)

    os.makedirs(hash_dir, exist_ok=True)

    map_file = os.path.join(hash_dir, "inline-js-hash-map.txt")

    # clear previous map
    open(map_file, "w").close()

    # print("[+] Extracting inline JavaScript...")

    total = extract_inline_js(html_dir, js_output_dir, map_file)

    # print("\n[✓] DONE")
    print(f" Inline JS extracted : {total}\n")
    # print(f" JS Directory        : targets/{domain}/download/inline-js/")
    # print(f" Hash Map            : targets/{domain}/download/hash-map/inline-js-hash-map.txt")


if __name__ == "__main__":
    main()
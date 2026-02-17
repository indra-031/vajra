#!/usr/bin/env python3
# extraction/html/libraries-html.py
# Extract JS libraries and versions ONLY from HTML files (no inline JS parsing)
# Reads from : targets/<DOMAIN>/download/html
# Writes to  : targets/<DOMAIN>/extraction/html/libraries.json

import os
import re
import sys
import json
from urllib.parse import urlparse


# ---------------- CONFIG ----------------

LIB_PATTERNS = [
    r"(jquery)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(react)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(vue)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(angular)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(axios)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(lodash)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(moment)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(bootstrap)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
]

LIB_REGEX = [re.compile(p, re.IGNORECASE) for p in LIB_PATTERNS]


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


# ---------------- CORE ----------------

def extract_libraries(html_dir: str, out_file: str) -> int:
    results = []

    for root, _, files in os.walk(html_dir):
        for filename in files:
            if not filename.endswith((".html", ".htm")):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    html = f.read()

                for regex in LIB_REGEX:
                    for match in regex.finditer(html):
                        results.append({
                            "library": match.group(1).lower(),
                            "version": match.group(2),
                            "file": os.path.relpath(path, html_dir)
                        })

            except Exception:
                continue

    if not results:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as o:
        json.dump(results, o, indent=2)

    return len(results)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: libraries-html.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    html_dir = os.path.join(base_targets, domain, "download", "html")

    if not os.path.isdir(html_dir):
        print("[!] HTML download directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "html",
        "libraries.json"
    )

    print("[+] Extracting Libraries from HTML")
    count = extract_libraries(html_dir, out_file)

    if count == 0:
        print("[!] No libraries found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} hits")
        # print(f" Saved to: targets/{domain}/extraction/html/libraries.json")


if __name__ == "__main__":
    main()

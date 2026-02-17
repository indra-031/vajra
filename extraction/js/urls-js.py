#!/usr/bin/env python3
# extraction/js/urls-js.py
# Extract absolute URLs from JS files (allowed schemes only)
# Reads from : targets/<DOMAIN>/download/js
# Writes to  : targets/<DOMAIN>/extraction/js/urls.txt

import os
import re
import sys
from urllib.parse import urlparse


# ---------------- CONFIG ----------------

ALLOWED_SCHEMES = (
    "http:",
    "https:",
    "ws:",
    "wss:",
    "ftp:",
    "file:",
    "data:",
    "blob:",
    "javascript:",
    "chrome:",
    "moz-extension:",
)

URL_REGEX = re.compile(
    r"""
    \b
    (
        (?:http|https|ws|wss|ftp|file|data|blob|javascript|chrome|moz-extension)
        :
        [^\s"'<>]+
    )
    """,
    re.VERBOSE | re.IGNORECASE
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def clean_url(u: str) -> str:
    return u.rstrip(";,)]}>")


# ---------------- CORE ----------------

def extract_urls(js_dir: str, out_file: str) -> int:
    urls = set()

    for root, _, files in os.walk(js_dir):
        for filename in files:
            if not filename.endswith(".js"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                for match in URL_REGEX.findall(data):
                    cleaned = clean_url(match)
                    urls.add(cleaned)

            except Exception:
                continue

    if not urls:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        for u in sorted(urls):
            f.write(u + "\n")

    return len(urls)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: urls-js.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")

    if not os.path.isdir(js_dir):
        print("[!] JS directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "js",
        "urls.txt"
    )

    print("[+] Extracting URLs from JS")
    count = extract_urls(js_dir, out_file)

    if count == 0:
        print("[!] No URLs found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} URLs")
        # print(f" Saved to: targets/{domain}/extraction/js/urls.txt")


if __name__ == "__main__":
    main()

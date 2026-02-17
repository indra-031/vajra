#!/usr/bin/env python3
# extraction/html/urls-html.py
# Extract absolute URLs from HTML attributes only
# Reads from : targets/<DOMAIN>/download/html
# Writes to  : targets/<DOMAIN>/extraction/html/urls.txt

import os
import sys
import re
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

ATTR_URL_REGEX = re.compile(
    r"""(?:href|src|action|data-[a-z0-9\-]+)=["']([^"'>]+)""",
    re.I
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def looks_like_allowed_url(u: str) -> bool:
    return any(u.startswith(scheme) for scheme in ALLOWED_SCHEMES)


# ---------------- CORE ----------------

def extract_urls(html_dir: str, out_file: str) -> int:
    urls = set()

    for root, _, files in os.walk(html_dir):
        for filename in files:
            if not filename.endswith((".html", ".htm")):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    html = f.read()

                for u in ATTR_URL_REGEX.findall(html):
                    if looks_like_allowed_url(u):
                        urls.add(u)

            except Exception:
                continue

    if not urls:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as o:
        for u in sorted(urls):
            o.write(u + "\n")

    return len(urls)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: urls-html.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    html_dir = os.path.join(base_targets, domain, "download", "html")

    if not os.path.isdir(html_dir):
        print("[!] HTML directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "html",
        "urls.txt"
    )

    print("[+] Extracting URLs from HTML")
    count = extract_urls(html_dir, out_file)

    if count == 0:
        print("[!] No URLs found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} URLs")
        # print(f" Saved to: targets/{domain}/extraction/html/urls.txt")


if __name__ == "__main__":
    main()

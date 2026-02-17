#!/usr/bin/env python3
# extraction/html/paths-html.py
# Extract practical website paths ONLY from HTML (no inline JS parsing)
# Reads from : targets/<DOMAIN>/download/html
# Writes to  : targets/<DOMAIN>/extraction/html/paths.txt

import os
import re
import sys
from urllib.parse import urlparse


# ---------------- REGEX ----------------

ATTR_PATH_REGEX = re.compile(
    r"""(?:href|src|action|data-[a-z0-9\-]+)=["']([^"'>]+)""",
    re.I
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def looks_like_real_path(p: str) -> bool:
    if (
        "/" in p[1:]
        or "." in p
        or "?" in p
        or "=" in p
        or any(c.isdigit() for c in p)
    ):
        return True
    return False


def clean_and_add(p: str, paths: set):
    if not p.startswith("/"):
        return

    if p.startswith(("/^", "/(", "/[")):
        return

    if p.startswith("//"):
        return

    if not looks_like_real_path(p):
        return

    if p.startswith("/www."):
        return

    if re.match(r"^/[^/]+\.com(/|$)", p):
        return

    paths.add(p)


# ---------------- CORE ----------------

def extract_paths(html_dir: str, out_file: str) -> int:
    paths = set()

    for root, _, files in os.walk(html_dir):
        for filename in files:
            if not filename.endswith((".html", ".htm")):
                continue

            full_path = os.path.join(root, filename)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    html = f.read()

                # فقط attributeهای HTML
                for attr in ATTR_PATH_REGEX.findall(html):
                    clean_and_add(attr, paths)

            except Exception:
                continue

    if not paths:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as o:
        for p in sorted(paths):
            o.write(p + "\n")

    return len(paths)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: paths-html.py <domain>")
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
        "paths.txt"
    )

    print("[+] Extracting Paths from HTML")
    count = extract_paths(html_dir, out_file)

    if count == 0:
        print("[!] No paths found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} paths")
        # print(f" Saved to: targets/{domain}/extraction/html/paths.txt")


if __name__ == "__main__":
    main()

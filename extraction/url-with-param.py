#!/usr/bin/env python3
# extraction/filter-params.py

import os
import sys
from urllib.parse import urlparse

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def read_lines(file_path: str):
    if not os.path.isfile(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().splitlines()
    except Exception:
        return []


def is_in_scope(url: str, domain: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if host == domain:
            return True

        if host.endswith("." + domain):
            return True

        return False
    except Exception:
        return False


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: filter-params.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target).lower()

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../targets")
    )

    target_base = os.path.join(base_targets, domain)

    input_files = [
        os.path.join(target_base, "download", "merge-urls.txt"),
        os.path.join(target_base, "extraction", "merge", "urls-merge.txt"),
        os.path.join(target_base, "extraction", "merge", "links-merge.txt"),
        os.path.join(target_base, "extraction", "merge", "paths-merge.txt"),
    ]

    print("[+] Running URLs with param")

    all_urls = set()

    for file_path in input_files:
        lines = read_lines(file_path)
        for line in lines:
            url = line.strip()
            if url:
                all_urls.add(url)

    # print(f" ├─ Total collected: {len(all_urls)}")

    urls_with_params = []

    for url in all_urls:
        if not is_in_scope(url, domain):
            continue

        if "?" in url:
            urls_with_params.append(url)

    if not urls_with_params:
        print("[!] No in-scope URLs with parameters found")
        sys.exit(0)

    output_file = os.path.join(
        target_base,
        "extraction",
        "merge",
        "urls-with-param.txt"
    )

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for url in sorted(urls_with_params):
            f.write(url + "\n")

    print(f"[✓] Found {len(urls_with_params)} in-scope URLs with parameters\n")
    # print(f" → targets/{domain}/extraction/merge/urls-with-param.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# attack/online/attack-urls.py

import os
import sys
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    if not target.startswith("http"):
        target = "https://" + target
    return urlparse(target).netloc


def read_urls_from_file(path: str) -> set:
    urls = set()

    if not os.path.exists(path):
        return urls

    with open(path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line:
                urls.add(line)

    return urls


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: attack-urls.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    # 🔥 correct base path (two levels up)
    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    # -------- source files --------

    source_files = [
        os.path.join(base_targets_dir, domain, "download", "merge-urls.txt"),
        os.path.join(base_targets_dir, domain, "extraction", "merge", "urls-merge.txt"),
        os.path.join(base_targets_dir, domain, "extraction", "merge", "urls-with-param.txt"),
    ]

    all_urls = set()
    existing_files = 0

    for file_path in source_files:
        if os.path.exists(file_path):
            existing_files += 1
            urls = read_urls_from_file(file_path)
            all_urls.update(urls)

    # -------- output path --------

    output_dir = os.path.join(
        base_targets_dir,
        domain,
        "attack",
        "online",
        "attack-urls"
    )

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "urls.txt")

    with open(output_path, "w") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    # -------- summary --------

    print("====================================")
    print(" Vajra - Attack URL Merger")
    print("====================================")
    print(f" Target : {domain}")
    print(f" Source Files Found : {existing_files}/{len(source_files)}")
    print(f" Total Unique URLs  : {len(all_urls)}")
    print("------------------------------------")
    print(f"[+] Output saved : targets/{domain}/attack/online/attack-urls/urls.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# discovery/merge.py

import os
import sys
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def collect_txt_files(base_dir: str) -> list:
    files = []

    for root, _, filenames in os.walk(base_dir):
        for name in filenames:
            if not name.endswith(".txt"):
                continue

            path = os.path.join(root, name)
            if os.path.isfile(path):
                files.append(path)

    return files


def read_urls(files: list) -> set:
    results = set()

    for file_path in files:
        try:
            with open(file_path, "r", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("http"):
                        results.add(line)
        except Exception:
            continue

    return results


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: merge.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../targets")
    )

    discovery_dir = os.path.join(
        base_targets,
        domain,
        "discovery"
    )

    if not os.path.isdir(discovery_dir):
        print("[!] discovery directory not found")
        sys.exit(0)

    download_dir = os.path.join(
        base_targets,
        domain,
        "download"
    )
    os.makedirs(download_dir, exist_ok=True)

    output_file = os.path.join(download_dir, "merge-urls.txt")

    # print("[+] Collecting discovery files...")
    txt_files = collect_txt_files(discovery_dir)

    if not txt_files:
        print("[!] No .txt files found inside discovery/")
        sys.exit(0)

    print(f"[+] Files found: {len(txt_files)}")

    merged_urls = read_urls(txt_files)

    if not merged_urls:
        print("[!] No valid URLs found")
        sys.exit(0)

    with open(output_file, "w") as f:
        for url in sorted(merged_urls):
            f.write(url + "\n")

    # print("\n[✓] MERGE DONE")
    print(f"[+] Merge Done Unique URLs : {len(merged_urls)}")
    # print(f" Output      : targets/{domain}/download/merge-urls.txt")


if __name__ == "__main__":
    main()

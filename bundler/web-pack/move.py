#!/usr/bin/env python3
# bundler/move.py

import os
import sys
from urllib.parse import urlparse
import shutil


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: move_reversed_to_download.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    source_dir = os.path.join(
        base_targets_dir,
        domain,
        "bundler",
        "webpack-reverse"
    )

    destination_dir = os.path.join(
        base_targets_dir,
        domain,
        "download",
        "js"
    )

    if not os.path.exists(source_dir):
        # print("[!] Source directory not found.")
        sys.exit(0)

    os.makedirs(destination_dir, exist_ok=True)

    copied = 0

    # recursive walk
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if not file.endswith(".js"):
                continue

            src_path = os.path.join(root, file)
            dst_path = os.path.join(destination_dir, file)

            shutil.copy2(src_path, dst_path)
            copied += 1

    # print("====================================")
    # print(" Vajra - Move Reversed JS")
    # print("====================================")
    # print(f" Target : {domain}")
    print(f" JS Files Copied : {copied}")
    # print("------------------------------------")
    # print(f"[+] Destination : targets/{domain}/download/js/")


if __name__ == "__main__":
    main()

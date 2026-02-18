#!/usr/bin/env python3

import os
import sys
from urllib.parse import urlparse


# ----------------------------
# Helpers
# ----------------------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def get_project_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "../../"))


# ----------------------------
# Main
# ----------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python parameter.py <domain>")
        return  # ⬅️ no exit(1)

    domain = normalize_domain(sys.argv[1])
    project_root = get_project_root()

    source_file = os.path.join(
        project_root,
        "targets",
        domain,
        "extraction",
        "merge",
        "parameters-merge.txt"
    )

    script_dir = os.path.dirname(os.path.abspath(__file__))
    wordlist_file = os.path.join(script_dir, "wordlist-parameter.txt")

    if not os.path.isfile(source_file):
        print(f"[!] No parameters file found for {domain} — skipping.")
        return  # ⬅️ graceful skip

    os.makedirs(script_dir, exist_ok=True)

    # Read existing wordlist
    existing_words = set()
    if os.path.isfile(wordlist_file):
        with open(wordlist_file, "r", encoding="utf-8") as f:
            existing_words = {
                line.strip()
                for line in f
                if line.strip()
            }

    # Read new params
    with open(source_file, "r", encoding="utf-8") as f:
        new_words = {
            line.strip()
            for line in f
            if line.strip()
        }

    unique_new_words = new_words - existing_words

    if unique_new_words:
        with open(wordlist_file, "a", encoding="utf-8") as f:
            for word in sorted(unique_new_words):
                f.write(word + "\n")

    total_count = len(existing_words) + len(unique_new_words)

    print("\n[✓] Wordlist update completed")
    print(f"[+] New parameters added: {len(unique_new_words)}")
    print(f"[+] Total parameters in wordlist: {total_count}")


if __name__ == "__main__":
    main()

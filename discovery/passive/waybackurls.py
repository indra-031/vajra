#!/usr/bin/env python3
# discovery/passive/wayback.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_wayback(domain: str) -> list:
    try:
        result = subprocess.check_output(
            [
                "waybackurls",
                "-no-subs",
                domain
            ],
            stderr=subprocess.DEVNULL,
            text=True
        )

        urls = [
            line.strip()
            for line in result.splitlines()
            if line.strip().lower().endswith((".js", ".html", ".htm"))
        ]

        # Remove duplicates while preserving order
        return list(dict.fromkeys(urls))

    except Exception:
        return []


def save_output(urls: list, base_targets_dir: str, domain: str):
    out_dir = os.path.join(
        base_targets_dir,
        domain,
        "discovery",
        "passive",
        "wayback"
    )

    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, "wayback.txt")

    with open(out_file, "w") as f:
        f.write("\n".join(urls))

    return out_file


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: wayback.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    urls = run_wayback(domain)

    if not urls:
        print("[!] No Wayback URLs found")
        sys.exit(0)

    out_file = save_output(urls, base_targets_dir, domain)

    print(f"[+] Wayback URLs saved: {len(urls)}")
    # print(f"[+] Path: targets/{domain}/discovery/passive/wayback/wayback.txt")


if __name__ == "__main__":
    main()

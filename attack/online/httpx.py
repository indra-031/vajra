#!/usr/bin/env python3
# attack/online/httpx-runner.py

import os
import sys
import subprocess
from urllib.parse import urlparse

HTTPX_BIN = os.path.expanduser("~/go/bin/httpx")

def normalize_domain(target: str) -> str:
    if not target.startswith("http"):
        target = "https://" + target
    return urlparse(target).netloc

def main():
    if len(sys.argv) != 2:
        print("Usage: httpx-runner.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    urls_path = os.path.join(
        base_dir,
        domain,
        "attack",
        "online",
        "attack-urls",
        "urls.txt"
    )

    output_dir = os.path.join(
        base_dir,
        domain,
        "attack",
        "online",
        "httpx"
    )

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "alive.txt")

    if not os.path.exists(urls_path):
        print("[!] urls.txt not found.")
        sys.exit(1)

    print(f"[+] Fast scanning {domain} ...")

    cmd = [
        HTTPX_BIN,
        "-l", urls_path,
        "-silent",
        "-fc", "404",      # filter 404
        "-no-color",
        "-threads", "300",
        "-rl", "1000",
        "-timeout", "5",
        "-retries", "0",
        "-o", output_file
    ]

    subprocess.run(cmd)

    print(f"[+] Done. Saved to targets/{domain}/attack/online/httpx/alive.txt")

if __name__ == "__main__":
    main()

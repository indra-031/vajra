#!/usr/bin/env python3
# discovery/passive/getjs.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_getjs(target: str) -> list:
    try:
        cmd = [
            "getJS",
            "-url", target,
            "-complete",
            "-resolve",
            "-threads", "10",
            "-timeout", "10s"
        ]

        result = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            text=True
        )

        # Remove duplicates while preserving order
        return list(dict.fromkeys(
            line.strip() for line in result.splitlines() if line.strip()
        ))

    except Exception:
        return []


def save_output(urls: list, base_targets_dir: str, domain: str):
    out_dir = os.path.join(
        base_targets_dir,
        domain,
        "discovery",
        "passive",
        "getjs"
    )

    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, "getjs_urls.txt")

    with open(out_file, "w") as f:
        f.write("\n".join(urls))

    return out_file


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: getjs.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    urls = run_getjs(target)

    if not urls:
        print("[!] No JS URLs found")
        sys.exit(0)

    out_file = save_output(urls, base_targets_dir, domain)

    print(f"[+] getJS URLs saved: {len(urls)}")
    # print(f"[+] Path: targets/{domain}/discovery/passive/getjs/getjs_urls.txt")


if __name__ == "__main__":
    main()

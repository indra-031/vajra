#!/usr/bin/env python3
# discovery/active/gospider.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_gospider_stream(target: str, domain: str, out_file: str) -> int:
    cmd = [
        "gospider",
        "-s", target,

        # crawl control
        "-d", "3",
        "-c", "10",
        "-t", "20",
        "-m", "10",

        # safe sources
        "--robots",
        "--sitemap",

        # js parsing
        "--js",

        # stability
        "--no-redirect",
        "--quiet"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1
    )

    count = 0
    seen = set()

    with open(out_file, "w") as f:
        for line in proc.stdout:
            line = line.strip()
            if not line.startswith("http"):
                continue

            parsed = urlparse(line)
            if parsed.netloc != domain:
                continue

            if line in seen:
                continue

            seen.add(line)
            count += 1
            f.write(line + "\n")

            print(f"\r[+] Gospider found {count} URLs", end="", flush=True)

    proc.wait()
    print()

    return count


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: gospider.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    base_dir = os.path.join(
        base_targets,
        domain,
        "discovery",
        "active",
        "gospider"
    )

    os.makedirs(base_dir, exist_ok=True)

    out_file = os.path.join(base_dir, "gospider_urls.txt")

    print("[+] Running Gospider (realtime mode)")
    total = run_gospider_stream(target, domain, out_file)

    if total == 0:
        print("[!] No Gospider output")
        sys.exit(0)

    print("\n[✓] DONE")
    print(f" URLs found : {total}")
    print(f" Saved to   : targets/{domain}/discovery/active/gospider/gospider_urls.txt")


if __name__ == "__main__":
    main()

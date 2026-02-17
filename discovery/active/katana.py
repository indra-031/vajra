#!/usr/bin/env python3
# discovery/active/katana.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_katana_stream(target: str, out_file: str) -> int:
    cmd = [
        "katana",
        "-u", target,

        # crawling
        "-jc",
        "-xhr",
        "-kf", "robotstxt",
        "-d", "3",

        # stability
        "-c", "15",
        "-p", "5",
        "-rl", "100",
        "-timeout", "10",

        # filters
        "-ef", "woff,woff2,ttf,png,jpg,jpeg,svg,gif,css",

        "-silent"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1
    )

    count = 0

    with open(out_file, "w") as f:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            count += 1
            f.write(line + "\n")

            print(f"\r[+] Katana found {count} URLs", end="", flush=True)

    proc.wait()
    print()

    return count


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: katana.py <target>")
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
        "katana"
    )

    os.makedirs(base_dir, exist_ok=True)

    out_file = os.path.join(base_dir, "katana_urls.txt")

    # print("[+] Running Katana (realtime mode)")
    total = run_katana_stream(target, out_file)

    if total == 0:
        print("[!] No Katana output")
        sys.exit(0)

    # print("\n[✓] DONE")
    # print(f" URLs found : {total}")
    # print(f" Saved to : targets/{domain}/discovery/active/katana/katana_urls.txt")


if __name__ == "__main__":
    main()

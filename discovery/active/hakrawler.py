#!/usr/bin/env python3
# discovery/active/hakrawler.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_hakrawler_stream(target: str, out_file: str) -> int:
    cmd = [
        "hakrawler",
        "-url", target,
        "-depth", "2",
        "-plain",
        "-u"  # unique urls
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

            print(f"\r[+] Hakrawler found {count} URLs", end="", flush=True)

    proc.wait()
    print()

    return count


def extract_js(url_file: str, js_file: str) -> int:
    count = 0

    with open(url_file, "r") as infile, open(js_file, "w") as outfile:
        for line in infile:
            line = line.strip().lower()

            if line.endswith(".js"):
                outfile.write(line + "\n")
                count += 1

    return count


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: hakrawler.py <target>")
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
        "hakrawler"
    )

    os.makedirs(base_dir, exist_ok=True)

    urls_file = os.path.join(base_dir, "hakrawler_urls.txt")
    js_file = os.path.join(base_dir, "hakrawler_js.txt")

    print("[+] Running Hakrawler (realtime mode)")
    total_urls = run_hakrawler_stream(target, urls_file)

    if total_urls == 0:
        print("[!] No Hakrawler output")
        sys.exit(0)

    total_js = extract_js(urls_file, js_file)

    print("\n[✓] DONE")
    print(f" URLs found : {total_urls}")
    print(f" JS found   : {total_js}")
    print(f" Saved to   : targets/{domain}/discovery/active/hakrawler/")


if __name__ == "__main__":
    main()

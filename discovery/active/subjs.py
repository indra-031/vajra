#!/usr/bin/env python3
# discovery/active/subjs.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def collect_all_urls(discovery_path: str) -> list:
    urls = set()

    for root, _, files in os.walk(discovery_path):
        for file in files:
            if not file.endswith(".txt"):
                continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("http"):
                            urls.add(line)
            except Exception:
                continue

    return sorted(urls)


def run_subjs(input_file: str, output_file: str) -> int:
    cmd = [
        "subjs",
        "-i", input_file,
        "-c", "20",
        "-t", "20"
    ]

    try:
        result = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            text=True
        )
    except subprocess.CalledProcessError:
        return 0

    js_urls = list(dict.fromkeys(
        line.strip() for line in result.splitlines() if line.strip()
    ))

    with open(output_file, "w") as f:
        f.write("\n".join(js_urls))

    return len(js_urls)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: subjs.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    discovery_path = os.path.join(
        base_targets,
        domain,
        "discovery"
    )

    active_subjs_dir = os.path.join(
        discovery_path,
        "active",
        "subjs"
    )

    os.makedirs(active_subjs_dir, exist_ok=True)

    temp_input = os.path.join(active_subjs_dir, "all_discovery_urls.txt")
    output_file = os.path.join(active_subjs_dir, "subjs_urls.txt")

    # print("[+] Collecting URLs from discovery tree...")
    all_urls = collect_all_urls(discovery_path)

    if not all_urls:
        print("[!] No URLs found in discovery directory")
        sys.exit(0)

    with open(temp_input, "w") as f:
        f.write("\n".join(all_urls))

    print(f"[+] Total unique URLs collected: {len(all_urls)}")
    # print("[+] Running subjs...")

    total_js = run_subjs(temp_input, output_file)

    if total_js == 0:
        print("[!] No JS URLs found by subjs")
        sys.exit(0)

    # print("\n[✓] DONE")
    print(f" JS found : {total_js}")
    # print(f" Saved to : targets/{domain}/discovery/active/subjs/subjs_urls.txt")


if __name__ == "__main__":
    main()

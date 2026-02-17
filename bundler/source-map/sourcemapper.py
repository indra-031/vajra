#!/usr/bin/env python3
# bundler/source-map/sourcemapper.py

import os
import sys
import subprocess
from urllib.parse import urlparse

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def load_urls(file_path: str) -> list:
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r") as f:
        return list(set(
            line.strip() for line in f
            if line.strip().startswith("http") and ".js" in line
        ))


def run_sourcemapper(js_url: str, output_dir: str) -> bool:
    try:
        subprocess.run(
            [
                "sourcemapper",
                "-jsurl", js_url,
                "-output", output_dir
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=40
        )
        return os.path.exists(output_dir) and os.listdir(output_dir)
    except:
        return False


def save_results(results: list, base_targets_dir: str, domain: str):
    out_dir = os.path.join(
        base_targets_dir,
        domain,
        "bundler",
        "source-map",
        "sourcemapper"
    )

    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, "exposed.txt")

    with open(out_file, "w") as f:
        if not results:
            f.write("No exposed sourcemaps found.\n")
        else:
            for r in results:
                f.write(r + "\n")

    return out_file


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: sourcemapper_from_urls.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    urls_file = os.path.join(
        base_targets_dir,
        domain,
        "extraction",
        "download",
        "merge-urls.txt"
    )

    js_urls = load_urls(urls_file)

    if not js_urls:
        print("[!] No JS URLs found")
        sys.exit(0)

    exposed = []

    for js in js_urls:
        safe_name = js.replace("https://", "").replace("http://", "").replace("/", "_")

        output_dir = os.path.join(
            base_targets_dir,
            domain,
            "bundler",
            "source-map",
            "sourcemapper",
            safe_name
        )

        success = run_sourcemapper(js, output_dir)

        if success:
            exposed.append(js)

    save_results(exposed, base_targets_dir, domain)

    # print("====================================")
    # print(" Vajra - Sourcemap From Collected URLs")
    # print("====================================")
    # print(f" Target            : {domain}")
    print(f" JS Files Checked  : {len(js_urls)}")
    print(f" Exposed Maps      : {len(exposed)}")
    # print("------------------------------------")
    # print(f"[+] Results saved  : targets/{domain}/discovery/webpack/sourcemapper/exposed.txt")


if __name__ == "__main__":
    main()

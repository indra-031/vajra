#!/usr/bin/env python3
# bundler/webpack/detect.py

import os
import sys
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

TIMEOUT = 10
HEADERS = {
    "User-Agent": "Vajra-Webpack-Detector"
}

WEBPACK_PATTERNS = [
    "__webpack_require__",
    "webpackChunk",
    "webpackJsonp",
    "window.webpack"
]

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def normalize_target(target: str) -> str:
    if not target.startswith("http"):
        return "https://" + target
    return target


def check_patterns(content: str) -> bool:
    return any(p in content for p in WEBPACK_PATTERNS)


def detect_webpack(url: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return False
    except:
        return False

    # Check HTML itself
    if check_patterns(r.text):
        return True

    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.find_all("script", src=True)

    for script in scripts:
        js_url = urljoin(url, script["src"])

        try:
            js_resp = requests.get(js_url, headers=HEADERS, timeout=TIMEOUT)
            if js_resp.status_code == 200:
                if check_patterns(js_resp.text):
                    return True
        except:
            continue

    return False


def save_output(result: bool, base_targets_dir: str, domain: str):
    # ✅ NEW PATH
    out_dir = os.path.join(
        base_targets_dir,
        domain,
        "bundler",
        "webpack",
        "detect"
    )

    os.makedirs(out_dir, exist_ok=True)

    detect_file = os.path.join(out_dir, "detect.txt")
    flag_file = os.path.join(out_dir, "web-pack-is-on.txt")

    with open(detect_file, "w") as f:
        f.write(f"Domain: {domain}\n")
        f.write(f"Webpack Detected: {result}\n")

    with open(flag_file, "w") as f:
        f.write("true\n" if result else "false\n")

    return detect_file


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: detect.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)
    target_url = normalize_target(target)

    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    result = detect_webpack(target_url)
    save_output(result, base_targets_dir, domain)

    # print("====================================")
    # print(" Vajra - Webpack Detection Module")
    # print("====================================")
    # print(f" Target            : {domain}")
    print(f" Webpack Detected  : {result}")
    # print("------------------------------------")
    # print(f"[+] Output saved   : targets/{domain}/bundler/webpack/detect/")

if __name__ == "__main__":
    main()

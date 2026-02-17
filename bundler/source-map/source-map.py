#!/usr/bin/env python3
# bundler/source-map/source_map.py

import os
import sys
import requests
from urllib.parse import urlparse, urljoin, urlunparse
from bs4 import BeautifulSoup

TIMEOUT = 5
HEADERS = {
    "User-Agent": "Vajra-SourceMap-Detector"
}

# ---------------- HELPERS ----------------

def normalize_target(target: str) -> str:
    if not target.startswith("http"):
        return "https://" + target
    return target


def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def get_frontpage_scripts(url: str) -> list:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
    except:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.find_all("script", src=True)

    return list(dict.fromkeys(
        urljoin(url, s["src"]) for s in scripts
    ))


def check_inline_map(js_url: str) -> str | None:
    try:
        r = requests.get(js_url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return None

        for line in r.text.splitlines():
            if "sourceMappingURL=" in line:
                map_name = line.split("sourceMappingURL=")[-1].strip()
                return urljoin(js_url, map_name)

    except:
        return None

    return None


def check_direct_map(js_url: str) -> str | None:
    try:
        parsed = urlparse(js_url)

        if not parsed.path.endswith(".js"):
            return None

        # Insert .map right after .js
        new_path = parsed.path + ".map"

        map_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            new_path,
            parsed.params,
            parsed.query,   # preserve query string
            parsed.fragment
        ))

        r = requests.head(
            map_url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        if r.status_code == 200:
            return map_url

    except:
        return None

    return None


def save_results(found_maps: list, base_targets_dir: str, domain: str, total_scripts: int):
    out_dir = os.path.join(
        base_targets_dir,
        domain,
        "bundler",
        "source-map",
        "detect"
    )

    os.makedirs(out_dir, exist_ok=True)

    summary_path = os.path.join(out_dir, "summary.txt")
    maps_path = os.path.join(out_dir, "found-maps.txt")
    status_path = os.path.join(out_dir, "is-open.txt")

    # summary
    with open(summary_path, "w") as f:
        f.write("Vajra - Source Map Detector\n")
        f.write("---------------------------------\n")
        f.write(f"Scripts Checked : {total_scripts}\n")
        f.write(f"Exposed Maps    : {len(found_maps)}\n")

    # found maps
    with open(maps_path, "w") as f:
        for m in found_maps:
            f.write(m + "\n")

    # status flag
    with open(status_path, "w") as f:
        f.write("true\n" if found_maps else "false\n")

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: source_map_detector.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    target_url = normalize_target(target)
    domain = normalize_domain(target)

    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    scripts = get_frontpage_scripts(target_url)
    found_maps = []

    for js in scripts:

        # Check inline sourceMappingURL
        inline_map = check_inline_map(js)
        if inline_map:
            found_maps.append(inline_map)
            break

        # Check direct .js.map
        direct_map = check_direct_map(js)
        if direct_map:
            found_maps.append(direct_map)
            break

    save_results(found_maps, base_targets_dir, domain, len(scripts))

    # print("====================================")
    # print(" Vajra - Source Map Detector")
    # print("====================================")
    # print(f" Target          : {domain}")
    # print(f" Scripts Checked : {len(scripts)}")
    print(f" SourceMap Open  : {bool(found_maps)}")
    # print("------------------------------------")
    # print(f"[+] Output saved : targets/{domain}/bundler/source-map-detector/")

if __name__ == "__main__":
    main()

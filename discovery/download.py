#!/usr/bin/env python3
# discovery/download.py

import os
import sys
import hashlib
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from collections import defaultdict
from tqdm import tqdm

requests.packages.urllib3.disable_warnings()


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def hash_name(value: str) -> str:
    return hashlib.md5(value.encode()).hexdigest()


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 Vajra"
    })
    return session


# ---------------- DOWNLOAD FUNCTIONS ----------------

def download_file(session, url, out_dir, map_file, lock, stats, extension):
    try:
        r = session.get(url, timeout=15, verify=False)

        with lock:
            stats[r.status_code] += 1

        if r.status_code != 200 or not r.content:
            return False

        file_hash = hash_name(url)

        if extension == "js":
            filename = f"{file_hash}.js"
        else:
            parsed = urlparse(url)
            name = os.path.basename(parsed.path)
            if not name or "." not in name:
                name = f"{file_hash[:12]}.html"
            filename = name

        file_path = os.path.join(out_dir, filename)

        with open(file_path, "wb") as f:
            f.write(r.content)

        with lock:
            with open(map_file, "a") as m:
                m.write(f"{file_hash} {url}\n")

        return True

    except Exception:
        with lock:
            stats["error"] += 1
        return False


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: download_artifacts.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../targets")
    )

    merge_file = os.path.join(
        base_targets,
        domain,
        "download",
        "merge-urls.txt"
    )

    if not os.path.isfile(merge_file):
        print("[!] merge-urls.txt not found")
        sys.exit(1)

    # -------- Paths --------

    download_base = os.path.join(base_targets, domain, "download")

    js_dir = os.path.join(download_base, "js")
    html_dir = os.path.join(download_base, "html")
    hash_dir = os.path.join(download_base, "hash-map")

    os.makedirs(js_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(hash_dir, exist_ok=True)

    js_map_file = os.path.join(hash_dir, "js-hash-map.txt")
    html_map_file = os.path.join(hash_dir, "html-hash-map.txt")

    open(js_map_file, "w").close()
    open(html_map_file, "w").close()

    # -------- Load URLs --------

    with open(merge_file, "r") as f:
        urls = {
            line.strip()
            for line in f
            if line.strip().startswith("http")
        }

    js_urls = [u for u in urls if u.lower().endswith(".js")]
    html_urls = [
        u for u in urls
        if u.lower().endswith(".html") or u.lower().endswith(".htm")
    ]

    print(f"[+] JS files   : {len(js_urls)}")
    print(f"[+] HTML files : {len(html_urls)}")

    # -------- Init --------

    session = create_session()
    lock = Lock()
    stats = defaultdict(int)

    # -------- Download JS --------

    if js_urls:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(
                    download_file,
                    session,
                    url,
                    js_dir,
                    js_map_file,
                    lock,
                    stats,
                    "js"
                )
                for url in js_urls
            ]

            for _ in tqdm(as_completed(futures),
                          total=len(futures),
                          desc="Downloading JS"):
                pass

    # -------- Download HTML --------

    if html_urls:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(
                    download_file,
                    session,
                    url,
                    html_dir,
                    html_map_file,
                    lock,
                    stats,
                    "html"
                )
                for url in html_urls
            ]

            for _ in tqdm(as_completed(futures),
                          total=len(futures),
                          desc="Downloading HTML"):
                pass

    # -------- Report --------

    # print("\n[✓] Download completed\n")

    print("Status Code Summary:")
    print(f" 200 : {stats[200]}")
    print(f" 400 : {stats[400]}")
    print(f" 403 : {stats[403]}")
    print(f" 404 : {stats[404]}")
    print(f" 429 : {stats[429]}")
    print(f" Error/Timeout : {stats['error']}")

    # print(f"\n JS Directory   → targets/{domain}/download/js/")
    # print(f" HTML Directory → targets/{domain}/download/html/")
    # print(f" JS Hash Map    → targets/{domain}/download/hash-map/js-hash-map.txt")
    # print(f" HTML Hash Map  → targets/{domain}/download/hash-map/html-hash-map.txt")


if __name__ == "__main__":
    main()

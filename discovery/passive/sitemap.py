#!/usr/bin/env python3
# discovery/passive/sitemap.py

import os
import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

TIMEOUT = 10
HEADERS = {
    "User-Agent": "Vajra-Sitemap-Checker"
}

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def normalize_target(target: str) -> str:
    if not target.startswith("http"):
        return "https://" + target
    return target.rstrip("/")


def fetch_xml(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200 and "xml" in r.headers.get("Content-Type", ""):
            return r.text
    except:
        pass
    return None


def parse_sitemap(xml_content: str):
    """
    Returns list of URLs from sitemap or sitemap index
    """
    urls = []

    try:
        root = ET.fromstring(xml_content)
    except:
        return urls

    # namespace handling
    namespace = ""
    if "}" in root.tag:
        namespace = root.tag.split("}")[0] + "}"

    # normal sitemap
    for url in root.findall(f".//{namespace}url/{namespace}loc"):
        urls.append(url.text.strip())

    # sitemap index
    for sitemap in root.findall(f".//{namespace}sitemap/{namespace}loc"):
        urls.append(sitemap.text.strip())

    return urls


def save_output(domain: str, base_targets_dir: str, found: bool, urls: list):
    out_dir = os.path.join(
        base_targets_dir,
        domain,
        "discovery",
        "passive",
        "sitemap"
    )

    os.makedirs(out_dir, exist_ok=True)

    status_file = os.path.join(out_dir, "status.txt")
    urls_file = os.path.join(out_dir, "urls.txt")

    with open(status_file, "w") as f:
        f.write("found\n" if found else "not-found\n")

    if found and urls:
        with open(urls_file, "w") as f:
            f.write("\n".join(sorted(set(urls))))

    return status_file


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: check_sitemap.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    domain = normalize_domain(target)
    base_url = normalize_target(target)

    base_targets_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    sitemap_url = base_url + "/sitemap.xml"

    xml_content = fetch_xml(sitemap_url)

    all_urls = []

    if not xml_content:
        save_output(domain, base_targets_dir, False, [])
        # print("====================================")
        # print(" Vajra - Sitemap Check")
        # print("====================================")
        # print(f" Target        : {domain}")
        print(" Sitemap       : NOT FOUND")
        # print("------------------------------------")
        # print(f"[+] Output saved : targets/{domain}/discovery/sitemap/")
        sys.exit(0)

    # First level
    urls = parse_sitemap(xml_content)

    # If it's sitemap index → crawl children
    for url in urls:
        if url.endswith(".xml"):
            child_xml = fetch_xml(url)
            if child_xml:
                child_urls = parse_sitemap(child_xml)
                all_urls.extend(child_urls)
        else:
            all_urls.append(url)

    save_output(domain, base_targets_dir, True, all_urls)

    # print("====================================")
    # print(" Vajra - Sitemap Check")
    # print("====================================")
    # print(f" Target        : {domain}")
    print(" Sitemap       : FOUND")
    print(f" URLs Collected: {len(all_urls)}")
    # print("------------------------------------")
    # print(f"[+] Output saved : targets/{domain}/discovery/passive/sitemap/")


if __name__ == "__main__":
    main()

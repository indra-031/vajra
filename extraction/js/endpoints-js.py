#!/usr/bin/env python3
# extraction/js/endpoints-js.py
# Extract clean endpoints from downloaded JS files
# Reads from : targets/<DOMAIN>/download/js
# Writes to  : targets/<DOMAIN>/extraction/js/endpoints.txt

import os
import re
import sys
from urllib.parse import urlparse


# ---------------- CONFIG ----------------

ENDPOINT_REGEX = re.compile(
    r'["\'`](/(?:[a-zA-Z0-9_\-/{}/\.]+)(?:\?[a-zA-Z0-9_\-&=%{}\.]+)?)["\'`]'
)

IGNORE_EXTENSIONS = (
    ".js", ".css", ".png", ".jpg", ".jpeg",
    ".svg", ".gif", ".ico", ".woff", ".woff2",
    ".map"
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def looks_real(ep: str) -> bool:
    if not ep.startswith("/"):
        return False

    if ep in ("/", "//"):
        return False

    if ep.lower().endswith(IGNORE_EXTENSIONS):
        return False

    # حذف مسیرهای خیلی کوتاه مثل /v1
    if ep.count("/") < 2:
        return False

    return True


def normalize(ep: str) -> str:
    return ep.split("?")[0]


# ---------------- CORE ----------------

def extract_endpoints(js_dir: str, out_file: str) -> int:
    results = set()

    for root, _, files in os.walk(js_dir):
        for filename in files:
            if not filename.endswith(".js"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                for ep in ENDPOINT_REGEX.findall(data):
                    if looks_real(ep):
                        results.add(normalize(ep))

            except Exception:
                continue

    if not results:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        for ep in sorted(results):
            f.write(ep + "\n")

    return len(results)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: endpoints-js.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")

    if not os.path.isdir(js_dir):
        print("[!] JS download directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "js",
        "endpoints.txt"
    )

    print("[+] Extracting JS Endpoints...")
    count = extract_endpoints(js_dir, out_file)

    if count == 0:
        print("[!] No endpoints found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} endpoints")
        # print(f" Saved to: targets/{domain}/extraction/js/endpoints.txt")


if __name__ == "__main__":
    main()

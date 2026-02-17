#!/usr/bin/env python3
# extraction/html/parameters-html.py
# Extract parameters ONLY from HTML (forms + attributes)
# Reads from : targets/<DOMAIN>/download/html
# Writes to  : targets/<DOMAIN>/extraction/html/parameters.txt

import os
import re
import sys
from urllib.parse import urlparse


# ---------------- REGEX ----------------

URL_PARAM_REGEX = re.compile(r"[?&]([a-zA-Z0-9_%\-]+)=")

FORM_ACTION_REGEX = re.compile(
    r"<form[^>]+action=[\"']([^\"'>]+)", re.I
)

INPUT_NAME_REGEX = re.compile(
    r"<(input|textarea|select)[^>]+name=[\"']([^\"'>]+)",
    re.I
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


# ---------------- CORE ----------------

def extract_parameters(html_dir: str, out_file: str) -> int:
    params = set()

    for root, _, files in os.walk(html_dir):
        for filename in files:
            if not filename.endswith((".html", ".htm")):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    html = f.read()

                # ---- form action parameters (?id=123) ----
                for action in FORM_ACTION_REGEX.findall(html):
                    params.update(URL_PARAM_REGEX.findall(action))

                # ---- input / select / textarea names ----
                for _, name in INPUT_NAME_REGEX.findall(html):
                    if len(name) > 1:
                        params.add(name)

                # ---- direct URL parameters inside HTML ----
                params.update(URL_PARAM_REGEX.findall(html))

            except Exception:
                continue

    if not params:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as o:
        for p in sorted(params):
            o.write(p + "\n")

    return len(params)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: parameters-html.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    html_dir = os.path.join(base_targets, domain, "download", "html")

    if not os.path.isdir(html_dir):
        print("[!] HTML directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "html",
        "parameters.txt"
    )

    print("[+] Extracting Parameters from HTML")
    count = extract_parameters(html_dir, out_file)

    if count == 0:
        print("[!] No parameters found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} parameters")
        # print(f" Saved to: targets/{domain}/extraction/html/parameters.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# extraction/html/fragments-html.py
# Extract URL fragments ONLY from HTML files (no inline JS parsing)
# Reads from : targets/<DOMAIN>/download/html
# Writes to  : targets/<DOMAIN>/extraction/html/fragments.txt

import os
import re
import sys
from urllib.parse import urlparse


# ---------------- REGEX ----------------

FRAGMENT_REGEX = re.compile(
    r'[a-zA-Z][a-zA-Z0-9+.-]*://[^\s"\'<>]+(#[a-zA-Z0-9/_\-\.]+)'
    r'|["\'](#[a-zA-Z0-9/_\-\.]{2,})["\']'
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def extract_fragments_from_text(text: str) -> set[str]:
    fragments = set()

    for match in FRAGMENT_REGEX.findall(text):
        if isinstance(match, tuple):
            for frag in match:
                if frag:
                    fragments.add(frag)
        elif match:
            fragments.add(match)

    return fragments


# ---------------- CORE ----------------

def process_html_directory(html_dir: str, out_file: str) -> int:
    output = []

    for root, _, files in os.walk(html_dir):
        for filename in files:
            if not filename.endswith((".html", ".htm")):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                fragments = extract_fragments_from_text(data)

                if not fragments:
                    continue

                rel_path = os.path.relpath(path, html_dir)

                output.append(f"=== {rel_path} ===")
                output.extend(sorted(fragments))
                output.append("")

            except Exception:
                continue

    if not output:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    return len(output)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: fragments-html.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    html_dir = os.path.join(base_targets, domain, "download", "html")

    if not os.path.isdir(html_dir):
        print("[!] HTML download directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "html",
        "fragments.txt"
    )

    print("[+] Extracting Fragments from HTML")
    count = process_html_directory(html_dir, out_file)

    if count == 0:
        print("[!] No fragments found")
    else:
        pass
        # print("[✓] DONE")
        # print(f" Saved to: targets/{domain}/extraction/html/fragments.txt")


if __name__ == "__main__":
    main()

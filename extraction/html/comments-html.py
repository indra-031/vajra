#!/usr/bin/env python3
# extraction/html/comments-html.py
# Extract ONLY HTML comments (<!-- -->)
# Reads from : targets/<DOMAIN>/download/html
# Writes to  : targets/<DOMAIN>/extraction/html/comments.txt

import os
import sys
import re
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


# ---------------- REGEX ----------------

HTML_COMMENT_REGEX = re.compile(r"<!--(.*?)-->", re.S)


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

                rel_path = os.path.relpath(path, html_dir)

                html_comments = [
                    "<!--" + c.strip() + "-->"
                    for c in HTML_COMMENT_REGEX.findall(data)
                    if c.strip()
                ]

                if not html_comments:
                    continue

                output.append(f"=== {rel_path} ===")
                output.extend(html_comments)
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
        print("Usage: comments-html.py <domain>")
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
        "comments.txt"
    )

    print("[+] Extracting HTML Comments")
    count = process_html_directory(html_dir, out_file)

    if count == 0:
        print("[!] No HTML comments found")
    else:
        pass
        # print("[✓] DONE")
        # print(f" Saved to: targets/{domain}/extraction/html/comments.txt")


if __name__ == "__main__":
    main()

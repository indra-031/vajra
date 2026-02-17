#!/usr/bin/env python3
# extraction/js/fragments-js.py
# Extract URL fragments from JavaScript files
# Reads from : targets/<DOMAIN>/download/js
# Writes to  : targets/<DOMAIN>/extraction/js/fragments.txt

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


def extract_fragments_from_js(js: str) -> list[str]:
    fragments = set()

    for match in FRAGMENT_REGEX.findall(js):
        # چون regex دو گروه داره، خروجی tuple میشه
        if isinstance(match, tuple):
            for frag in match:
                if frag and len(frag) > 1:
                    fragments.add(frag)
        elif match and len(match) > 1:
            fragments.add(match)

    return sorted(fragments)


# ---------------- CORE ----------------

def process_js_directory(js_dir: str, out_file: str) -> int:
    output = []

    for root, _, files in os.walk(js_dir):
        for filename in files:
            if not filename.endswith(".js"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                fragments = extract_fragments_from_js(data)
                if not fragments:
                    continue

                rel_path = os.path.relpath(path, js_dir)

                output.append(f"=== {rel_path} ===")
                output.extend(fragments)
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
        print("Usage: fragments-js.py <domain>")
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
        "fragments.txt"
    )

    print("[+] Extracting JS Fragments")
    count = process_js_directory(js_dir, out_file)

    if count == 0:
        print("[!] No fragments found")
    else:
        pass
        # print("[✓] DONE")
        # print(f" Saved to: targets/{domain}/extraction/js/fragments.txt")


if __name__ == "__main__":
    main()

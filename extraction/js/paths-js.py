#!/usr/bin/env python3
# extraction/js/paths-js.py
# Practical website path extractor from JS
# Reads from : targets/<DOMAIN>/download/js
# Writes to  : targets/<DOMAIN>/extraction/js/paths.txt

import os
import re
import sys
from urllib.parse import urlparse


# ---------------- REGEX ----------------

PATH_REGEX = re.compile(
    r"""
    (?<![\w$])
    (
        /[a-zA-Z0-9][a-zA-Z0-9\-._~/%?=&+#:@]*
    )
    """,
    re.VERBOSE
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def looks_like_real_path(p: str) -> bool:
    return (
        "/" in p[1:]
        or "." in p
        or "?" in p
        or "=" in p
        or any(c.isdigit() for c in p)
    )


def is_valid_path(p: str) -> bool:
    if not p.startswith("/"):
        return False

    # حذف regex literal
    if p.startswith(("/^", "/(", "/[")):
        return False

    # حذف comment
    if p.startswith("//"):
        return False

    # حذف junk تک‌کلمه‌ای
    if not looks_like_real_path(p):
        return False

    # حذف www.*
    if p.startswith("/www."):
        return False

    # حذف *.com یا *.com/...
    if re.match(r"^/[^/]+\.com(/|$)", p):
        return False

    # حذف مسیرهای خیلی کوتاه
    if len(p) < 3:
        return False

    return True


# ---------------- CORE ----------------

def extract_paths(js_dir: str, out_file: str) -> int:
    paths = set()

    for root, _, files in os.walk(js_dir):
        for filename in files:
            if not filename.endswith(".js"):
                continue

            full_path = os.path.join(root, filename)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                for p in PATH_REGEX.findall(data):
                    if is_valid_path(p):
                        paths.add(p)

            except Exception:
                continue

    if not paths:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        for p in sorted(paths):
            f.write(p + "\n")

    return len(paths)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: paths-js.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")

    if not os.path.isdir(js_dir):
        print("[!] JS directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "js",
        "paths.txt"
    )

    print("[+] Extracting Paths from JS")
    count = extract_paths(js_dir, out_file)

    if count == 0:
        print("[!] No paths found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} paths")
        # print(f" Saved to: targets/{domain}/extraction/js/paths.txt")


if __name__ == "__main__":
    main()

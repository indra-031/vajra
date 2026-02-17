#!/usr/bin/env python3
# bundler/reverse-webpack.py

import os
import sys
import re
import subprocess

WEBPACK_PATTERNS = [
    "__webpack_require__",
    "webpackChunk",
    "webpackJsonp"
]

# ---------------- UTIL ----------------

def read_flag(flag_path: str) -> bool:
    if not os.path.exists(flag_path):
        return False
    with open(flag_path) as f:
        return f.read().strip() == "true"


def is_webpack_bundle(content: str) -> bool:
    return any(p in content for p in WEBPACK_PATTERNS)


def beautify_js(input_path: str, output_path: str):
    try:
        subprocess.run(
            ["js-beautify", input_path, "-o", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except:
        with open(input_path) as src, open(output_path, "w") as dst:
            dst.write(src.read())


# ---------------- MODULE EXTRACTION ----------------

def extract_module_object(content: str):
    """
    Bracket-based extraction of webpack module object
    """
    match = re.search(r'\{\s*\d+\s*:\s*(function|\()', content)
    if not match:
        return None

    start = match.start()
    brace_count = 0

    for i in range(start, len(content)):
        if content[i] == "{":
            brace_count += 1
        elif content[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                return content[start:i+1]

    return None


def split_modules(module_blob: str, output_dir: str):
    pattern = re.compile(r'(\d+)\s*:\s*(function|\()')
    matches = list(pattern.finditer(module_blob))

    count = 0

    for i, match in enumerate(matches):
        module_id = match.group(1)
        start = match.start()

        end = matches[i+1].start() if i+1 < len(matches) else len(module_blob)

        module_code = module_blob[start:end]

        path = os.path.join(output_dir, f"{module_id}.js")
        with open(path, "w") as f:
            f.write(module_code)

        count += 1

    return count


# ---------------- STRING DEOBFUSCATION ----------------

def deobfuscate_strings(content: str):
    """
    Extract simple string array and replace references
    Example:
    var _0xabc = ["a","b"];
    console.log(_0xabc[0]);
    """

    array_pattern = re.search(r'var\s+(_0x[a-fA-F0-9]+)\s*=\s*\[(.*?)\];', content, re.DOTALL)

    if not array_pattern:
        return content, 0

    var_name = array_pattern.group(1)
    raw_array = array_pattern.group(2)

    strings = re.findall(r'"(.*?)"|\'(.*?)\'', raw_array)
    flat_strings = [s[0] if s[0] else s[1] for s in strings]

    replaced = 0

    for idx, value in enumerate(flat_strings):
        pattern = rf'{var_name}\[{idx}\]'
        content, n = re.subn(pattern, f'"{value}"', content)
        replaced += n

    # remove original array
    content = re.sub(rf'var\s+{var_name}\s*=\s*\[.*?\];', '', content, flags=re.DOTALL)

    return content, replaced


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: reverse-webpack.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]

    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    flag_path = os.path.join(
        base_dir, domain,
        "bundler", "webpack", "detect",
        "web-pack-is-on.txt"
    )

    if not read_flag(flag_path):
        # print("[!] Webpack not detected. Exiting.")
        sys.exit(0)

    download_dirs = [
        os.path.join(base_dir, domain, "download", "js"),
        os.path.join(base_dir, domain, "download", "inline-js")
    ]

    reverse_base = os.path.join(
        base_dir, domain,
        "bundler", "webpack-reverse"
    )

    raw_dir = os.path.join(reverse_base, "raw")
    beautified_dir = os.path.join(reverse_base, "beautified")
    modules_dir = os.path.join(reverse_base, "modules")
    deob_dir = os.path.join(reverse_base, "deobfuscated")

    for d in [raw_dir, beautified_dir, modules_dir, deob_dir]:
        os.makedirs(d, exist_ok=True)

    processed = 0
    extracted_total = 0
    string_replaced_total = 0

    for d in download_dirs:
        if not os.path.exists(d):
            continue

        for file in os.listdir(d):
            if not file.endswith(".js"):
                continue

            full_path = os.path.join(d, file)

            with open(full_path, "r", errors="ignore") as f:
                content = f.read()

            if not is_webpack_bundle(content):
                continue

            processed += 1

            # Save raw
            raw_path = os.path.join(raw_dir, file)
            with open(raw_path, "w") as f:
                f.write(content)

            # Beautify
            beautified_path = os.path.join(beautified_dir, file)
            beautify_js(raw_path, beautified_path)

            with open(beautified_path, "r", errors="ignore") as f:
                beautified_content = f.read()

            # Extract modules
            module_blob = extract_module_object(beautified_content)
            if module_blob:
                extracted = split_modules(module_blob, modules_dir)
                extracted_total += extracted

            # Deobfuscate
            deob_content, replaced = deobfuscate_strings(beautified_content)
            string_replaced_total += replaced

            deob_path = os.path.join(deob_dir, file)
            with open(deob_path, "w") as f:
                f.write(deob_content)

    # Summary
    summary_path = os.path.join(reverse_base, "summary.txt")
    with open(summary_path, "w") as f:
        f.write("Vajra - Advanced Webpack Reverse\n")
        f.write("---------------------------------\n")
        f.write(f"Bundles Processed   : {processed}\n")
        f.write(f"Modules Extracted   : {extracted_total}\n")
        f.write(f"Strings Replaced    : {string_replaced_total}\n")

    # print("====================================")
    # print(" Vajra - Advanced Webpack Reverse")
    # print("====================================")
    print(f" Bundles Processed : {processed}")
    print(f" Modules Extracted : {extracted_total}")
    print(f" Strings Decoded   : {string_replaced_total}")
    # print("------------------------------------")
    # print(f"[+] Output saved : targets/{domain}/bundler/webpack-reverse/")


if __name__ == "__main__":
    main()

import os
import re
import json
import sys
from urllib.parse import urlparse


# ---------------- PATTERNS ----------------

LIB_PATTERNS = [
    r"(jquery)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(react)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(vue)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(angular)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(axios)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(lodash)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(moment)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
    r"(bootstrap)[^\n]{0,80}?(\d+\.\d+(?:\.\d+)?)",
]

LIB_REGEX = [re.compile(p, re.IGNORECASE) for p in LIB_PATTERNS]


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


# ---------------- CORE ----------------

def extract_libraries(js_dir: str, out_file: str) -> int:
    seen = set()
    results = []

    for root, _, files in os.walk(js_dir):
        for filename in files:
            if not filename.endswith(".js"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                rel_path = os.path.relpath(path, js_dir)

                for regex in LIB_REGEX:
                    for match in regex.finditer(data):
                        lib = match.group(1).lower()
                        version = match.group(2)

                        key = (lib, version, rel_path)
                        if key in seen:
                            continue

                        seen.add(key)

                        results.append({
                            "library": lib,
                            "version": version,
                            "file": rel_path
                        })

            except Exception:
                continue

    if not results:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return len(results)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: libraries-inline-js.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "inline-js")

    if not os.path.isdir(js_dir):
        print("[!] inline-js download directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "inline-js",
        "libraries.json"
    )

    print("[+] Extracting Inline-JS Libraries")
    count = extract_libraries(js_dir, out_file)

    if count == 0:
        print("[!] No libraries detected")
    else:
        # print("[✓] DONE")
        print(f" Found {count} entries")
        # print(f" Saved to: targets/{domain}/extraction/inline-js/libraries.json")


if __name__ == "__main__":
    main()

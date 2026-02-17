#!/usr/bin/env python3
# analysis/dom/dom-map.py
# DOM Source/Sink Mapper
# Reads from :
#   targets/<DOMAIN>/download/js
#   targets/<DOMAIN>/download/inline-js
# Writes to :
#   targets/<DOMAIN>/attack/offline/dom/dom-map/

import os
import re
import json
import sys
from urllib.parse import urlparse

# ---------------- CONFIG ----------------

SOURCES = {
    "location": r"\blocation(\.|$)",
    "document_url": r"\bdocument\.(URL|documentURI|location)\b",
    "document_referrer": r"\bdocument\.referrer\b",
    "window_name": r"\bwindow\.name\b",
    "local_storage": r"\blocalStorage\b",
    "session_storage": r"\bsessionStorage\b",
    "postmessage_data": r"\bevent\.data\b"
}

SINKS = {
    "innerHTML": r"\.innerHTML\s*=",
    "outerHTML": r"\.outerHTML\s*=",
    "document_write": r"\bdocument\.write\s*\(",
    "insertAdjacentHTML": r"\.insertAdjacentHTML\s*\(",
    "eval": r"\beval\s*\(",
    "Function_constructor": r"\bFunction\s*\(",
    "setTimeout_string": r"\bsetTimeout\s*\(\s*['\"]",
    "location_assign": r"\blocation\s*=",
    "location_func": r"\blocation\.(assign|replace)\s*\(",
    "src_assign": r"\.src\s*=",
    "href_assign": r"\.href\s*="
}

SOURCE_REGEX = {k: re.compile(v) for k, v in SOURCES.items()}
SINK_REGEX = {k: re.compile(v) for k, v in SINKS.items()}

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc

# ---------------- CORE ----------------

def scan_directory(scan_dir: str, base_dir: str):
    results = []

    for root, _, files in os.walk(scan_dir):
        for filename in files:

            if not filename.endswith(".js"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                rel_path = os.path.relpath(path, base_dir)

                for lineno, line in enumerate(lines, start=1):

                    for name, regex in SOURCE_REGEX.items():
                        if regex.search(line):
                            results.append({
                                "file": rel_path,
                                "kind": "SOURCE",
                                "type": name,
                                "line": lineno,
                                "code": line.strip()
                            })

                    for name, regex in SINK_REGEX.items():
                        if regex.search(line):
                            results.append({
                                "file": rel_path,
                                "kind": "SINK",
                                "type": name,
                                "line": lineno,
                                "code": line.strip()
                            })

            except Exception:
                continue

    return results

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: dom-map.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")
    inline_js_dir = os.path.join(base_targets, domain, "download", "inline-js")

    if not os.path.isdir(js_dir) and not os.path.isdir(inline_js_dir):
        print("[!] JS directories not found")
        sys.exit(0)

    print("[+] Running DOM Map")

    all_results = {}

    # ---------- JS ----------
    if os.path.isdir(js_dir):
        # print(" ├─ Scanning js")
        results = scan_directory(js_dir, base_targets)
        if results:
            all_results["js"] = results

    # ---------- INLINE JS ----------
    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline-js")
        results = scan_directory(inline_js_dir, base_targets)
        if results:
            all_results["inline-js"] = results

    if not all_results:
        print("[!] No DOM sources/sinks found")
        return

    out_dir = os.path.join(
        base_targets,
        domain,
        "attack",
        "offline",
        "dom",
        "dom-map"
    )

    os.makedirs(out_dir, exist_ok=True)

    for key, data in all_results.items():
        out_file = os.path.join(out_dir, f"dom-map-{key}.json")

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # print("\n[✓] DONE")
    # print(f" Path : targets/{domain}/attack/offline/dom/dom-map/")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# secret/jsluice.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def collect_files(base_dir: str, ext: str) -> list[str]:
    results = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith(ext):
                results.append(os.path.join(root, f))
    return results


def run_jsluice(files: list[str], out_file: str) -> bool:
    if not files:
        return False

    cmd = ["jsluice", "secrets", "-c", "5"] + files

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    output = result.stdout.strip()

    if not output:
        return False

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output)

    return True


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: jsluice.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")
    inline_js_dir = os.path.join(base_targets, domain, "download", "inline-js")
    html_dir = os.path.join(base_targets, domain, "download", "html")

    if not any(os.path.isdir(d) for d in (js_dir, inline_js_dir, html_dir)):
        print("[!] No JS / HTML / inline-js directories found")
        sys.exit(1)

    out_dir = os.path.join(
        base_targets,
        domain,
        "secret",
        "jsluice"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running jsluice")

    # ---------- JS ----------
    if os.path.isdir(js_dir):
        # print(" ├─ Scanning JS")
        js_files = collect_files(js_dir, ".js")
        js_out = os.path.join(out_dir, "js.json")
        if run_jsluice(js_files, js_out):
            found = True

    # ---------- inline-js ----------
    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline-js")
        inline_files = collect_files(inline_js_dir, ".js")
        inline_out = os.path.join(out_dir, "inline-js.json")
        if run_jsluice(inline_files, inline_out):
            found = True

    # ---------- HTML (raw scan) ----------
    if os.path.isdir(html_dir):
        # print(" ├─ Scanning raw HTML files")
        html_files = collect_files(html_dir, ".html")
        html_out = os.path.join(out_dir, "html.json")
        if run_jsluice(html_files, html_out):
            found = True

    if not found:
        try:
            os.rmdir(out_dir)
        except:
            pass

        # print("[!] No secrets found")
    else:
        pass
        # print("\n[✓] DONE")
        # print(f" Path : targets/{domain}/secret/jsluice/")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# secret/shhgit.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_shhgit(scan_dir: str, config_path: str) -> str:
    cmd = [
        "shhgit",
        "-local", scan_dir,
        "-config-path", config_path,
        "-entropy-threshold", "0",
        "-silent"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.stdout.strip()


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: shhgit.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    targets_dir = os.path.join(project_root, "targets", domain)

    js_dir = os.path.join(targets_dir, "download", "js")
    inline_js_dir = os.path.join(targets_dir, "download", "inline-js")
    html_dir = os.path.join(targets_dir, "download", "html")

    if not any(os.path.isdir(d) for d in (js_dir, inline_js_dir, html_dir)):
        print("[!] No JS / HTML / inline-js directories found")
        sys.exit(1)

    config_path = os.path.join(project_root, "configs", "shhgit")

    out_dir = os.path.join(
        targets_dir,
        "secret",
        "shhgit"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running shhgit")

    # ---------- JS ----------
    if os.path.isdir(js_dir):
        # print(" ├─ Scanning JS")
        output = run_shhgit(js_dir, config_path)
        if output:
            with open(os.path.join(out_dir, "js.txt"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- inline-js ----------
    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline-js")
        output = run_shhgit(inline_js_dir, config_path)
        if output:
            with open(os.path.join(out_dir, "inline-js.txt"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # ---------- HTML ----------
    if os.path.isdir(html_dir):
        # print(" ├─ Scanning HTML")
        output = run_shhgit(html_dir, config_path)
        if output:
            with open(os.path.join(out_dir, "html.txt"), "w", encoding="utf-8") as f:
                f.write(output)
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
        # print(f" Path : targets/{domain}/secret/shhgit/")


if __name__ == "__main__":
    main()

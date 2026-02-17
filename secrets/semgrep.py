#!/usr/bin/env python3
# secret/semgrep.py

import os
import sys
import subprocess
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def run_semgrep(scan_dir: str, config_file: str) -> str:
    cmd = [
        "semgrep",
        "scan",
        scan_dir,
        "--config", config_file,
        "--json",
        "--quiet",
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
        print("Usage: semgrep.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    targets_dir = os.path.join(project_root, "targets")
    configs_dir = os.path.join(project_root, "configs", "semgrep")

    js_dir = os.path.join(targets_dir, domain, "download", "js")
    inline_js_dir = os.path.join(targets_dir, domain, "download", "inline-js")
    html_dir = os.path.join(targets_dir, domain, "download", "html")

    if not any(os.path.isdir(d) for d in (js_dir, inline_js_dir, html_dir)):
        print("[!] No JS / HTML / inline-js directories found")
        sys.exit(1)

    out_dir = os.path.join(
        targets_dir,
        domain,
        "secret",
        "semgrep"
    )

    os.makedirs(out_dir, exist_ok=True)

    found = False

    print("[+] Running Semgrep")

    # -------- JS --------
    if os.path.isdir(js_dir):
        # print(" ├─ Scanning JS")
        config = os.path.join(configs_dir, "js-secrets.yml")
        output = run_semgrep(js_dir, config)
        if output and output != '{"results": []}':
            with open(os.path.join(out_dir, "js.json"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # -------- inline-js --------
    if os.path.isdir(inline_js_dir):
        # print(" ├─ Scanning inline-js")
        config = os.path.join(configs_dir, "js-secrets.yml")
        output = run_semgrep(inline_js_dir, config)
        if output and output != '{"results": []}':
            with open(os.path.join(out_dir, "inline-js.json"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    # -------- HTML --------
    if os.path.isdir(html_dir):
        # print(" ├─ Scanning HTML")
        config = os.path.join(configs_dir, "html-secrets.yml")
        output = run_semgrep(html_dir, config)
        if output and output != '{"results": []}':
            with open(os.path.join(out_dir, "html.json"), "w", encoding="utf-8") as f:
                f.write(output)
            found = True

    if not found:
        try:
            os.rmdir(out_dir)
        except:
            pass

        # print("[!] No findings")
    else:
        pass
        # print("\n[✓] DONE")
        # print(f" Path : targets/{domain}/secret/semgrep/")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# analysis/dom/dom-xss.py
# DOM XSS Detector (based on dom-flow)
# Reads from :
#   targets/<DOMAIN>/attack/offline/dom/dom-flow/dom-flow.json
# Writes to :
#   targets/<DOMAIN>/attack/offline/dom/dom-xss/dom-xss.json

import os
import sys
import json
from urllib.parse import urlparse

# ---------------- CONFIG ----------------

DANGEROUS_SINKS = {
    "innerHTML",
    "outerHTML",
    "document_write",
    "insertAdjacentHTML",
    "eval",
    "Function_constructor",
    "setTimeout_string",
}

URL_SINKS = {
    "location_assign",
    "location_func",
    "src_assign",
    "href_assign",
}

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc

def load_json(path: str):
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def generate_payload(sink_type: str):

    if sink_type in DANGEROUS_SINKS:
        return "<img src=x onerror=alert(1)>"

    if sink_type in URL_SINKS:
        return "javascript:alert(1)"

    return "alert(1)"

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: dom-xss.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../targets")
    )

    flow_file = os.path.join(
        base_targets,
        domain,
        "attack",
        "offline",
        "dom",
        "dom-flow",
        "dom-flow.json"
    )

    flows = load_json(flow_file)

    if not flows:
        print("[!] dom-flow.json not found or empty")
        sys.exit(0)

    print("[+] Analyzing DOM XSS")

    vulns = []

    for flow in flows:

        if flow["confidence"] not in ("HIGH", "MEDIUM"):
            continue

        sink = flow["sink_type"]

        if sink not in DANGEROUS_SINKS and sink not in URL_SINKS:
            continue

        payload = generate_payload(sink)

        severity = "HIGH" if sink in DANGEROUS_SINKS else "MEDIUM"

        vulns.append({
            "file": flow["file"],
            "source_type": flow["source_type"],
            "source_line": flow["source_line"],
            "sink_type": sink,
            "sink_line": flow["sink_line"],
            "confidence": flow["confidence"],
            "severity": severity,
            "recommended_payload": payload
        })

    if not vulns:
        print("[!] No probable DOM XSS found")
        return

    out_dir = os.path.join(
        base_targets,
        domain,
        "attack",
        "offline",
        "dom",
        "dom-xss"
    )

    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, "dom-xss.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(vulns, f, indent=2)

    # print("\n[✓] DONE")
    # print(f" Path : targets/{domain}/attack/offline/dom/dom-xss/dom-xss.json")
    print(f" Potential DOM XSS : {len(vulns)}")

if __name__ == "__main__":
    main()

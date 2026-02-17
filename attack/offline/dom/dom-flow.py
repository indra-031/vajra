#!/usr/bin/env python3
# analysis/dom/dom-flow.py
# DOM Flow Correlator (Source → Sink proximity)
# Reads from :
#   targets/<DOMAIN>/attack/offline/dom/dom-map/
# Writes to :
#   targets/<DOMAIN>/attack/offline/dom/dom-flow/dom-flow.json

import os
import sys
import json
from urllib.parse import urlparse

# ---------------- CONFIG ----------------

MAX_LINE_DISTANCE = 50

# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc

def confidence(distance: int) -> str:
    if distance <= 10:
        return "HIGH"
    if distance <= 30:
        return "MEDIUM"
    return "LOW"

def load_json(path: str):
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: dom-flow.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../targets")
    )

    dom_map_dir = os.path.join(
        base_targets,
        domain,
        "attack",
        "offline",
        "dom",
        "dom-map"
    )

    if not os.path.isdir(dom_map_dir):
        print("[!] dom-map directory not found")
        sys.exit(0)

    map_files = [
        os.path.join(dom_map_dir, f)
        for f in os.listdir(dom_map_dir)
        if f.endswith(".json")
    ]

    if not map_files:
        print("[!] dom-map outputs not found")
        sys.exit(0)

    print("[+] Running DOM Flow Analysis")

    # ---------- Load all findings ----------
    all_findings = []
    for file_path in map_files:
        all_findings.extend(load_json(file_path))

    # ---------- Group by file ----------
    grouped = {}
    for item in all_findings:
        grouped.setdefault(item["file"], []).append(item)

    flows = []
    seen = set()

    for file_path, entries in grouped.items():

        sources = [e for e in entries if e["kind"] == "SOURCE"]
        sinks = [e for e in entries if e["kind"] == "SINK"]

        if not sources or not sinks:
            continue

        for src in sources:
            for sink in sinks:

                dist = abs(src["line"] - sink["line"])

                if dist > MAX_LINE_DISTANCE:
                    continue

                fingerprint = (
                    file_path,
                    src["line"],
                    sink["line"]
                )

                if fingerprint in seen:
                    continue

                seen.add(fingerprint)

                flows.append({
                    "file": file_path,
                    "source_type": src["type"],
                    "source_line": src["line"],
                    "sink_type": sink["type"],
                    "sink_line": sink["line"],
                    "line_distance": dist,
                    "confidence": confidence(dist)
                })

    if not flows:
        print("[!] No DOM flows found")
        return

    # ---------- Output ----------
    out_dir = os.path.join(
        base_targets,
        domain,
        "attack",
        "offline",
        "dom",
        "dom-flow"
    )

    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, "dom-flow.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(flows, f, indent=2)

    # ---------- Stats ----------
    high = sum(1 for x in flows if x["confidence"] == "HIGH")
    med = sum(1 for x in flows if x["confidence"] == "MEDIUM")
    low = sum(1 for x in flows if x["confidence"] == "LOW")

    # print("\n[✓] DONE")
    # print(f" Path : targets/{domain}/attack/offline/dom/dom-flow/dom-flow.json")
    print(f" Total flows : {len(flows)}")
    print(f" HIGH : {high} | MEDIUM : {med} | LOW : {low}")

if __name__ == "__main__":
    main()

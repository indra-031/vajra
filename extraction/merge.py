#!/usr/bin/env python3
# extraction/merge.py
# Vajra Extraction Merger (Incremental / Deduplicated)

import sys
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    if not target.startswith("http"):
        target = f"https://{target}"
    return urlparse(target).netloc


def build_targets_base() -> Path:
    return Path(__file__).resolve().parents[1] / "targets"


def collect_files(base_dir: Path) -> List[Path]:
    return [
        f for f in base_dir.rglob("*")
        if f.is_file()
        and "merge" not in f.parts
        and f.suffix.lower() in (".txt", ".json")
    ]


# ---------------- TXT MERGE ----------------

def merge_txt(files: List[Path], output_file: Path) -> int:
    seen = set()
    added = 0

    # Load existing
    if output_file.exists():
        try:
            for line in output_file.read_text(errors="ignore").splitlines():
                stripped = line.strip()
                if stripped:
                    seen.add(stripped)
        except Exception:
            pass

    # Process new files
    for file in files:
        try:
            for line in file.read_text(errors="ignore").splitlines():
                stripped = line.strip()
                if not stripped or stripped in seen:
                    continue
                seen.add(stripped)
                with output_file.open("a", encoding="utf-8") as f:
                    f.write(stripped + "\n")
                added += 1
        except Exception:
            continue

    return added


# ---------------- JSON MERGE ----------------

def merge_json(files: List[Path], output_file: Path) -> int:
    merged = []
    seen = set()
    added = 0

    # Load existing
    if output_file.exists():
        try:
            existing = json.loads(output_file.read_text())
            if isinstance(existing, list):
                for item in existing:
                    key = json.dumps(item, sort_keys=True)
                    seen.add(key)
                    merged.append(item)
        except Exception:
            pass

    # Process new files
    for file in files:
        try:
            data = json.loads(file.read_text())
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]

        for item in items:
            key = json.dumps(item, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
            added += 1

    # Save only if new items exist
    if added > 0:
        output_file.write_text(json.dumps(merged, indent=2))

    return added


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: merge.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])
    base_targets = build_targets_base()
    target_dir = base_targets / domain
    extraction_dir = target_dir / "extraction"

    if not extraction_dir.exists():
        print("[!] extraction directory not found")
        sys.exit(1)

    print("[+] Running Extraction Merge")

    files = collect_files(extraction_dir)

    if not files:
        print("[!] No extraction files found")
        sys.exit(0)

    # Group by filename
    grouped: Dict[str, List[Path]] = {}
    for file in files:
        grouped.setdefault(file.name, []).append(file)

    merge_dir = extraction_dir / "merge"
    merge_dir.mkdir(parents=True, exist_ok=True)

    total_added = 0
    processed_files = 0

    for name, file_list in grouped.items():
        out_name = name.replace(".", "-merge.")
        out_file = merge_dir / out_name

        if name.endswith(".txt"):
            added = merge_txt(file_list, out_file)

        elif name.endswith(".json"):
            added = merge_json(file_list, out_file)

        else:
            continue

        if added > 0:
            print(f" [+] {out_name} → {added} new items")
            total_added += added
            processed_files += 1

    if total_added == 0:
        print("[!] Nothing new to merge")
        return

    # print("\n[✓] DONE")
    # print(f" Path : targets/{domain}/extraction/merge/")
    print(f" Files updated : {processed_files}")
    print(f" Total new items : {total_added}")


if __name__ == "__main__":
    main()

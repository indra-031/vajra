#!/usr/bin/env python3
# extraction/html/emails-html.py
# Extract email addresses ONLY from HTML files (no inline JS parsing)
# Reads from : targets/<DOMAIN>/download/html
# Writes to  : targets/<DOMAIN>/extraction/html/emails.txt

import os
import sys
import re
from urllib.parse import urlparse


# ---------------- REGEX ----------------

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def looks_valid(email: str) -> bool:
    return not email.lower().endswith((
        ".png", ".jpg", ".jpeg", ".gif", ".svg"
    ))


# ---------------- CORE ----------------

def extract_emails(html_dir: str, out_file: str) -> int:
    emails = set()

    for root, _, files in os.walk(html_dir):
        for filename in files:
            if not filename.endswith((".html", ".htm")):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                for email in EMAIL_REGEX.findall(data):
                    if looks_valid(email):
                        emails.add(email)

            except Exception:
                continue

    if not emails:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as o:
        for email in sorted(emails):
            o.write(email + "\n")

    return len(emails)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: emails-html.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    html_dir = os.path.join(base_targets, domain, "download", "html")

    if not os.path.isdir(html_dir):
        print("[!] HTML directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "html",
        "emails.txt"
    )

    print("[+] Extracting Emails from HTML")
    count = extract_emails(html_dir, out_file)

    if count == 0:
        print("[!] No emails found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} emails")
        # print(f" Saved to: targets/{domain}/extraction/html/emails.txt")


if __name__ == "__main__":
    main()

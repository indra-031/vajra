#!/usr/bin/env python3
# extraction/js/email-js.py
# Extract email addresses from downloaded JS files
# Reads from : targets/<DOMAIN>/download/js
# Writes to  : targets/<DOMAIN>/extraction/js/emails.txt

import os
import sys
import re
from urllib.parse import urlparse


# ---------------- REGEX ----------------

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

JUNK_EXTENSIONS = (
    ".png", ".jpg", ".jpeg",
    ".gif", ".svg", ".webp",
    ".ico"
)


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def is_valid_email(email: str) -> bool:
    email = email.lower()

    # Skip obvious junk like image filenames
    if email.endswith(JUNK_EXTENSIONS):
        return False

    # Skip source map artifacts
    if email.endswith(".map"):
        return False

    return True


# ---------------- CORE ----------------

def extract_emails(js_dir: str, out_file: str) -> int:
    emails = set()

    for root, _, files in os.walk(js_dir):
        for filename in files:
            if not filename.endswith(".js"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                for email in EMAIL_REGEX.findall(data):
                    if is_valid_email(email):
                        emails.add(email)

            except Exception:
                continue

    if not emails:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        for email in sorted(emails):
            f.write(email + "\n")

    return len(emails)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: email-js.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "js")

    if not os.path.isdir(js_dir):
        print("[!] JS directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "js",
        "emails.txt"
    )

    print("[+] Extracting Emails from JS")
    count = extract_emails(js_dir, out_file)

    if count == 0:
        print("[!] No emails found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} emails")
        # print(f" Saved to: targets/{domain}/extraction/js/emails.txt")


if __name__ == "__main__":
    main()

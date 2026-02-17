import os
import re
import sys
from urllib.parse import urlparse


# ---------------- REGEX ----------------

URL_PARAM_REGEX = re.compile(r"[?&]([a-zA-Z0-9_%\-]{2,})=")
BODY_PARAM_REGEX = re.compile(r"([a-zA-Z0-9_%-]{2,})\s*=")
OBJECT_PARAM_REGEX = re.compile(r"{([^}]{1,300})}")
LOCATION_REGEX = re.compile(r"location\.(search|hash)")

INLINE_SCRIPT_REGEX = re.compile(
    r"<script[^>]*>(.*?)</script>", re.I | re.S
)

# پارامترهای بی‌ارزش رایج
IGNORE_PARAMS = {
    "var", "let", "const", "if", "for", "while",
    "true", "false", "null", "undefined"
}


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


def clean_param(p: str) -> str | None:
    p = p.strip()

    if len(p) < 2:
        return None

    if p.lower() in IGNORE_PARAMS:
        return None

    if p.isdigit():
        return None

    return p


# ---------------- CORE ----------------

def extract_from_text(text: str, params: set):
    # URL params (?id=&token=)
    for p in URL_PARAM_REGEX.findall(text):
        cp = clean_param(p)
        if cp:
            params.add(cp)

    # Object / body params
    for block in OBJECT_PARAM_REGEX.findall(text):
        for p in BODY_PARAM_REGEX.findall(block):
            cp = clean_param(p)
            if cp:
                params.add(cp)

    # location.search / hash usage
    if LOCATION_REGEX.search(text):
        params.add("location_search")
        params.add("location_hash")


def extract_parameters(js_dir: str, html_dir: str, out_file: str) -> int:
    params = set()

    # -------- JS FILES --------
    if os.path.isdir(js_dir):
        for root, _, files in os.walk(js_dir):
            for filename in files:
                if not filename.endswith(".js"):
                    continue

                path = os.path.join(root, filename)

                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        extract_from_text(f.read(), params)
                except Exception:
                    continue

    # -------- HTML INLINE JS --------
    if os.path.isdir(html_dir):
        for root, _, files in os.walk(html_dir):
            for filename in files:
                if not filename.endswith((".html", ".htm")):
                    continue

                path = os.path.join(root, filename)

                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        html = f.read()

                    for script in INLINE_SCRIPT_REGEX.findall(html):
                        extract_from_text(script, params)

                except Exception:
                    continue

    if not params:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        for p in sorted(params):
            f.write(p + "\n")

    return len(params)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: parameters-inline-js.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "inline-js")
    html_dir = os.path.join(base_targets, domain, "download", "html")

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "inline-js",
        "parameters.txt"
    )

    print("[+] Extracting Parameters (Jinline-js + inline HTML)...")
    count = extract_parameters(js_dir, html_dir, out_file)

    if count == 0:
        print("[!] No parameters found")
    else:
        # print("[✓] DONE")
        print(f" Found {count} parameters")
        # print(f" Saved to: targets/{domain}/extraction/inline-js/parameters.txt")


if __name__ == "__main__":
    main()

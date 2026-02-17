import os
import sys
from urllib.parse import urlparse


# ---------------- HELPERS ----------------

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc


# ---------------- CORE LOGIC ----------------

def extract_comments_from_js(js: str) -> list[str]:
    comments = []

    NORMAL = 0
    LINE_COMMENT = 1
    BLOCK_COMMENT = 2
    STRING_SINGLE = 3
    STRING_DOUBLE = 4
    TEMPLATE = 5

    state = NORMAL
    buf = ""

    i = 0
    n = len(js)

    while i < n:
        c = js[i]
        nxt = js[i + 1] if i + 1 < n else ""

        if state == NORMAL:
            if c == "/" and nxt == "/":
                state = LINE_COMMENT
                buf = ""
                i += 1
            elif c == "/" and nxt == "*":
                state = BLOCK_COMMENT
                buf = ""
                i += 1
            elif c == "'":
                state = STRING_SINGLE
            elif c == '"':
                state = STRING_DOUBLE
            elif c == "`":
                state = TEMPLATE

        elif state == LINE_COMMENT:
            if c == "\n":
                if buf.strip():
                    comments.append("//" + buf.strip())
                state = NORMAL
            else:
                buf += c

        elif state == BLOCK_COMMENT:
            if c == "*" and nxt == "/":
                if buf.strip():
                    comments.append("/*" + buf.strip() + "*/")
                state = NORMAL
                i += 1
            else:
                buf += c

        elif state == STRING_SINGLE:
            if c == "\\":
                i += 1
            elif c == "'":
                state = NORMAL

        elif state == STRING_DOUBLE:
            if c == "\\":
                i += 1
            elif c == '"':
                state = NORMAL

        elif state == TEMPLATE:
            if c == "\\":
                i += 1
            elif c == "`":
                state = NORMAL

        i += 1

    # Handle EOF line comment
    if state == LINE_COMMENT and buf.strip():
        comments.append("//" + buf.strip())

    return comments


def process_js_directory(js_dir: str, out_file: str) -> int:
    output = []

    for root, _, files in os.walk(js_dir):
        for filename in files:
            if not filename.endswith(".js"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()

                comments = extract_comments_from_js(data)
                if not comments:
                    continue

                rel_path = os.path.relpath(path, js_dir)
                output.append(f"=== {rel_path} ===")
                output.extend(comments)
                output.append("")

            except Exception:
                continue

    if not output:
        return 0

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    return len(output)


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: comments-inline-js.py <domain>")
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])

    base_targets = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../targets")
    )

    js_dir = os.path.join(base_targets, domain, "download", "inline-js")

    if not os.path.isdir(js_dir):
        print("[!] inline-js download directory not found")
        sys.exit(0)

    out_file = os.path.join(
        base_targets,
        domain,
        "extraction",
        "inline-js",
        "comments.txt"
    )

    print("[+] Extracting Inline-JS comments")
    count = process_js_directory(js_dir, out_file)

    if count == 0:
        print("[!] No comments found")
    else:
        pass
        # print("[✓] DONE")
        # print(f" Saved to: targets/{domain}/extraction/inline-js/comments.txt")


if __name__ == "__main__":
    main()

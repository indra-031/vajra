import os
import sys
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import defaultdict, Counter

def normalize_domain(target: str) -> str:
    parsed = urlparse(target if target.startswith("http") else f"https://{target}")
    return parsed.netloc

def find_project_root():
    """Find the project root (vajra/) dynamically"""
    current = os.path.abspath(os.getcwd())
    while current and os.path.basename(current) != "vajra":
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current

def is_static_file(path: str) -> bool:
    if '.' not in path:
        return False
    ext = path.rsplit('.', 1)[-1].lower()
    static_exts = {
        'js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico',
        'woff', 'woff2', 'ttf', 'eot', 'map', 'pdf', 'doc', 'docx',
        'xml', 'json', 'txt', 'csv', 'mp4', 'mp3', 'webm', 'webp',
        'otf', 'ttf', 'eot', 'woff', 'woff2'
    }
    return ext in static_exts

def is_html_file(path: str) -> bool:
    if '.' not in path:
        return False
    ext = path.rsplit('.', 1)[-1].lower()
    return ext in {'html', 'htm', 'php', 'asp', 'aspx', 'jsp'}

def is_invalid_url(url: str) -> bool:
    if not url or url.startswith('://') or url.startswith('///'):
        return True
    parsed = urlparse(url)
    if not parsed.scheme and not parsed.netloc:
        if url.startswith('/'):
            return False
        return True
    if parsed.scheme and not parsed.netloc:
        return True
    return False

def is_target_domain(url: str, target_domain: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return False
    return parsed.netloc == target_domain or parsed.netloc.endswith(f".{target_domain}")

def simplify_path(path: str) -> str:
    """
    Simplify path by keeping only first level
    /api/v1/users/123/profile → /api/
    /skldjscd/xxxx → /skldjscd/
    """
    if not path or path == '/':
        return '/'
    
    parts = path.lstrip('/').split('/')
    if not parts or not parts[0]:
        return '/'
    
    # فقط سطح اول رو نگه دار
    return f"/{parts[0]}"

def normalize_url(url: str, target_domain: str = None) -> tuple:
    if is_invalid_url(url):
        return (None, None)
    
    parsed = urlparse(url)
    
    # اگه فقط path باشه (با / شروع میشه)
    if not parsed.scheme and not parsed.netloc and url.startswith('/'):
        if target_domain:
            full_url = f"https://{target_domain}{url}"
            parsed = urlparse(full_url)
            url = full_url
    
    # اگه هیچ scheme و netloc نداره ولی با / شروع نمیشه
    elif not parsed.scheme and not parsed.netloc:
        if target_domain:
            full_url = f"https://{target_domain}/{url}"
            parsed = urlparse(full_url)
            url = full_url
    
    path = parsed.path.rstrip('/')
    params = parse_qs(parsed.query)
    
    # ساده‌سازی path - فقط سطح اول
    simplified_path = simplify_path(path)
    
    # ساخت URL نهایی
    if params:
        param_names = '|'.join(sorted(params.keys()))
        key = f"{parsed.scheme}://{parsed.netloc}{simplified_path}|{param_names}"
        new_url = f"{parsed.scheme}://{parsed.netloc}{simplified_path}"
        if parsed.query:
            new_url += f"?{parsed.query}"
        return (key, new_url)
    else:
        key = f"{parsed.scheme}://{parsed.netloc}{simplified_path}"
        new_url = f"{parsed.scheme}://{parsed.netloc}{simplified_path}"
        return (key, new_url)

def main():
    if len(sys.argv) < 2:
        target_input = input("Enter target domain (e.g. http://test.com or test.com): ").strip()
    else:
        target_input = sys.argv[1].strip()

    domain = normalize_domain(target_input)
    print(f"Normalized domain: {domain}")

    project_root = find_project_root()
    print(f"Project root detected: {project_root}")

    base_dir = os.path.join(project_root, "targets", domain)

    relative_files = [
        "discovery/passive/wayback/wayback.txt",
        "discovery/passive/gau/gau.txt",
        "discovery/passive/sitemap/urls.txt",
        "discovery/passive/getjs/getjs_urls.txt",
        "discovery/active/katana/katana_urls.txt",
        "discovery/active/subjs/all_discovery_urls.txt",
        "discovery/active/subjs/subjs_urls.txt",
        "extraction/merge/urls-with-param.txt",
        "extraction/merge/paths-merge.txt",
        "extraction/merge/endpoints-merge.txt",
        "download/merge-urls.txt",
    ]

    seen_keys = set()
    all_urls = set()
    found_files = 0
    total_raw = 0
    duplicates_removed = 0
    invalid_removed = 0
    static_files_removed = 0
    html_files_removed = 0
    skipped_domains = 0
    endpoints_fixed = 0

    print("\nReading files...")
    for rel_path in relative_files:
        file_path = os.path.join(base_dir, rel_path)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line.strip() for line in f if line.strip()]
                    total_raw += len(lines)
                    
                    new_urls = []
                    skipped = 0
                    static_skip = 0
                    html_skip = 0
                    invalid_skip = 0
                    domain_skip = 0
                    endpoint_fix = 0
                    
                    for url in lines:
                        # اگه URL با / شروع میشه و دامنه نداره، دامنه رو اضافه کن
                        if url.startswith('/') and not url.startswith('//'):
                            url = f"https://{domain}{url}"
                            endpoint_fix += 1
                        elif not url.startswith('http') and not url.startswith('/'):
                            # اگه path خالص هست (مثلاً "about/contact")
                            url = f"https://{domain}/{url}"
                            endpoint_fix += 1
                        
                        if is_invalid_url(url):
                            invalid_skip += 1
                            continue
                        
                        parsed = urlparse(url)
                        
                        if parsed.netloc and not is_target_domain(url, domain):
                            domain_skip += 1
                            continue
                        
                        key, normalized = normalize_url(url, domain)
                        
                        if key is None:
                            invalid_skip += 1
                            continue
                        
                        if is_static_file(parsed.path) and not parse_qs(parsed.query):
                            static_skip += 1
                            if key not in seen_keys:
                                seen_keys.add(key)
                                new_urls.append(normalized)
                                all_urls.add(normalized)
                            else:
                                skipped += 1
                            continue
                        
                        if is_html_file(parsed.path) and not parse_qs(parsed.query):
                            html_skip += 1
                            if key not in seen_keys:
                                seen_keys.add(key)
                                new_urls.append(normalized)
                                all_urls.add(normalized)
                            else:
                                skipped += 1
                            continue
                        
                        if key not in seen_keys:
                            seen_keys.add(key)
                            new_urls.append(normalized)
                            all_urls.add(normalized)
                        else:
                            skipped += 1
                    
                    static_files_removed += static_skip
                    html_files_removed += html_skip
                    invalid_removed += invalid_skip
                    duplicates_removed += skipped
                    skipped_domains += domain_skip
                    endpoints_fixed += endpoint_fix
                    found_files += 1
                    
                    status_parts = []
                    if new_urls:
                        status_parts.append(f"+{len(new_urls)} URLs")
                    if skipped:
                        status_parts.append(f"{skipped} dupes")
                    if static_skip:
                        status_parts.append(f"{static_skip} static")
                    if html_skip:
                        status_parts.append(f"{html_skip} HTML")
                    if invalid_skip:
                        status_parts.append(f"{invalid_skip} invalid")
                    if domain_skip:
                        status_parts.append(f"{domain_skip} other domains")
                    if endpoint_fix:
                        status_parts.append(f"{endpoint_fix} endpoints fixed")
                    
                    if status_parts:
                        print(f"✓ {rel_path} → {', '.join(status_parts)}")
                    else:
                        print(f"✓ {rel_path} → no new URLs")
                        
            except Exception as e:
                print(f"✗ Error reading {rel_path}: {e}")
        else:
            print(f"⚠ Not found: {rel_path}")

    if not all_urls:
        print("\n❌ No URLs found in any file!")
        return

    output_dir = os.path.join(base_dir, "attack/online/lfi")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "urls.txt")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in sorted(all_urls):
                f.write(url + '\n')

        print("\n" + "="*60)
        print(f"✅ Merge completed successfully!")
        print(f"Total raw URLs     : {total_raw:,}")
        print(f"Endpoints fixed    : {endpoints_fixed:,}")
        print(f"Other domains      : {skipped_domains:,}")
        print(f"Invalid URLs       : {invalid_removed:,}")
        print(f"Static files merged: {static_files_removed:,}")
        print(f"HTML files merged  : {html_files_removed:,}")
        print(f"Duplicates removed : {duplicates_removed:,}")
        print(f"Unique endpoints   : {len(all_urls):,}")
        print(f"Files processed    : {found_files}/{len(relative_files)}")
        print(f"Output saved to    : {output_file}")
        print("="*60)

    except Exception as e:
        print(f"❌ Error writing output: {e}")

if __name__ == "__main__":
    main()
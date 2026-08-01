#!/usr/bin/env bash
# File: vajra.sh
# Vajra – JS Recon Orchestrator (MVP)

set -e

if [ $# -ne 1 ]; then
    echo "Usage: ./vajra.sh https://target.com"
    exit 1
fi

TARGET="$1"

echo "[+] Starting Vajra on $TARGET"
echo

# -------------------------
# WAF Detection
# -------------------------
echo "[+] Running Wafw00f"
python3 discovery/active/wafw00f.py "$TARGET"
echo

# -------------------------
# Bundler Detection
# -------------------------
echo "[+] Running Web Pack Detection"
python3 bundler/web-pack/detect.py "$TARGET"
echo

echo "[+] Running Source Map Detection"
python3  bundler/source-map/source-map.py "$TARGET"
echo

# -------------------------
# Passive JS Discovery
# -------------------------
echo "[+] Running GetJS"
python3 discovery/passive/getjs.py "$TARGET"
echo

echo "[+] Running GAU"
python3 discovery/passive/gau.py "$TARGET"
echo

echo "[+] Running Site Map"
python3 discovery/passive/sitemap.py "$TARGET"
echo

echo "[+] Running Waybackulrs"
python3 discovery/passive/waybackurls.py "$TARGET"
echo

# -------------------------
# Active JS Discovery
# -------------------------
echo "[+] Running Katana"
python3 discovery/active/katana.py "$TARGET"
echo

# echo "[+] Running GoSpider"
# python3 discovery/active/gospider.py "$TARGET"
# echo

# echo "[+] Running Hakrawler"
# python3 discovery/active/hakrawler.py "$TARGET"
# echo

echo "[+] Running SubJS"
python3 discovery/active/subjs.py "$TARGET"
echo

# -------------------------
# Download
# -------------------------
echo "[+] Running Merge"
python3 discovery/merge.py "$TARGET"
echo

echo "[+] Running Downloader"
python3 discovery/download.py "$TARGET"
echo

# python3 bundler/source-map/sourcemapper.py "$TARGET"
# echo

# python3 bundler/source-map/move.py "$TARGET"
# echo

python3 bundler/web-pack/reverse-webpack.py "$TARGET"
echo

python3 bundler/web-pack/move.py "$TARGET"
echo

# -------------------------
# Extraction Phase
# -------------------------
echo "[+] Extract Inline JS"
python3 extraction/html/inline-js.py "$TARGET"

echo "[+] Running HTML Modules"
python3 extraction/html/comments-html.py "$TARGET"
python3 extraction/html/emails-html.py "$TARGET"
python3 extraction/html/endpoints-html.py "$TARGET"
python3 extraction/html/fragments-html.py "$TARGET"
python3 extraction/html/libraries-html.py "$TARGET"
python3 extraction/html/parameters-html.py "$TARGET"
python3 extraction/html/paths-html.py "$TARGET"
python3 extraction/html/urls-html.py "$TARGET"
echo

echo "[+] Running JS Modules"
python3 extraction/js/comments-js.py "$TARGET"
python3 extraction/js/emails-js.py "$TARGET"
python3 extraction/js/endpoints-js.py "$TARGET"
python3 extraction/js/fragments-js.py "$TARGET"
python3 extraction/js/libraries-js.py "$TARGET"
python3 extraction/js/parameters-js.py "$TARGET"
python3 extraction/js/paths-js.py "$TARGET"
python3 extraction/js/urls-js.py "$TARGET"
echo

echo "[+] Running InlineJS Modules"
python3 extraction/inline-js/comments-inline-js.py "$TARGET"
python3 extraction/inline-js/emails-inline-js.py "$TARGET"
python3 extraction/inline-js/endpoints-inline-js.py "$TARGET"
python3 extraction/inline-js/fragments-inline-js.py "$TARGET"
python3 extraction/inline-js/libraries-inline-js.py "$TARGET"
python3 extraction/inline-js/parameters-inline-js.py "$TARGET"
python3 extraction/inline-js/paths-inline-js.py "$TARGET"
python3 extraction/inline-js/urls-inline-js.py "$TARGET"
echo


echo "[+] Running 3rd Modules"
# python3 extraction/linkfinder.py "$TARGET"
python3 extraction/xnlinkfinder.py "$TARGET"
echo


python3 extraction/merge.py "$TARGET"
python3 extraction/url-with-param.py "$TARGET"

echo "[+] Running Wordlists"
python3 wordlist/parameter/parameter.py "$TARGET"
# -------------------------
# Secrets Hunting
# -------------------------
echo "[+] Running Secret Scanners"
python3 secrets/shhgit.py "$TARGET"
python3 secrets/trufflehog.py "$TARGET"
python3 secrets/semgrep.py "$TARGET"
python3 secrets/secretfinder.py "$TARGET"
python3 secrets/jsluice.py "$TARGET"
python3 secrets/gitleaks.py "$TARGET"
python3 secrets/dumpsterdiver.py "$TARGET"
python3 secrets/detectsecret.py "$TARGET"
python3 secrets/vscan.py "$TARGET"
echo


# -------------------------
# Offline Attack
# -------------------------
# echo "[+] Running Offline Attacks"
# python3 attack/offline/dom/dom-map.py "$TARGET"
# python3 attack/offline/dom/dom-flow.py "$TARGET"
# python3 attack/offline/dom/dom-xss.py "$TARGET"
# python3 attack/offline/njsscan.py "$TARGET"
# python3 attack/offline/retirejs.py "$TARGET"

# -------------------------
# Online Attack
# -------------------------
echo "[+] Running Online Attacks"
echo "[+] Running X9 Scanner"
python3 attack/online/x9/urls.py "$TARGET"
python3 attack/online/x9/x9.py "$TARGET"

echo "[+] Running Dalfox"
python3 attack/online/dalfox/dalfox.py "$TARGET"

echo "[+] Running LFI Scanner"
python3 attack/online/lfi/merge.py "$TARGET"
python3 attack/online/lfi/lfi.py "$TARGET"

echo "[+] Vajra finished successfully"
echo "[+] Happy hunting ⚡"
echo "YOU CAN SEE THE RESULT IN targets DIRECTORY"

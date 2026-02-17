# ⚔️ VAJRA – JavaScript Recon Framework

> ⚡ Offensive JavaScript Recon & Analysis Framework  
> 🔥 Built for Bug Bounty Hunters & Red Teamers  
> 🕶️ From Discovery → Extraction → Secret Hunting → Offline Vulnerability Analysis

---

## How To Run?
```
bash vajra.sh target.com
```
**It may take a while so be patient (e.g. 1 hour).**

## 🧠 What is Vajra?

**Vajra** is a modular **JavaScript Recon framework** designed to automate deep JS analysis in web targets.

It focuses on:

- 🌐 URL & JS Discovery
- 📦 JS Download & Hash Mapping
- 🧩 Extraction (endpoints, params, paths, secrets, libraries)
- 🕵️ Secret Hunting
- 🧬 Source-map & Webpack Detection
- 🧱 WAF Detection
- 💣 Offline Vulnerability Scanning (retire.js & njsscan)

It creates a clean structured workspace per target under:

```
targets/<domain>/
```

---

# 🚀 Installation

## 1️⃣ Clone the repository

```bash
git clone https://github.com/indra-031/vajra.git
cd vajra/install
```

## 2️⃣ Run installer

```bash
python install.py
```

---

# ⚙️ Requirements

You need:

- 🐍 Python 3.10+
- 🐹 Go
- Node.js (for some tools)

## Install Python (Linux)

```bash
sudo apt install python3 python3-pip
```

## Install Go (Linux)

```bash
sudo apt install golang
```

Or manually:

```bash
wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

Verify:

```bash
python3 --version
go version
```

---

# 🗂️ Project Structure

```
attack/
bundler/
configs/
discovery/
extraction/
secrets/
targets/
```

Each target gets its own structured workspace.

---

# 🔎 Discovery Phase

## 🔵 Active Discovery

- katana
- gospider
- hakrawler
- subjs

## 🟣 Passive Discovery

- gau
- waybackurls
- getJS
- sitemap parser

## 🧱 WAF Detection

- wafw00f

---

# 📥 Download Phase

- JS collection
- Inline JS extraction
- HTML capture
- Hash mapping
- URL merging

---

# 🧬 Extraction Phase

Extracts:

- Endpoints
- Parameters
- Paths
- URLs
- Comments
- Emails
- Fragments
- Libraries

Using:

- xnLinkFinder
- LinkFinder
- Custom parsers

---

# 🔐 Secret Hunting

Integrated tools:

- detect-secrets
- DumpsterDiver
- gitleaks
- jsluice
- SecretFinder
- semgrep
- shhgit
- trufflehog

Secrets are merged into:

```
targets/<domain>/extraction/merge/secrets-merge.txt
```

---

# 🧵 Bundler & Source Map Analysis

- sourcemapper
- Webpack detection
- Reverse webpack modules

Detect exposed source maps & hidden code.

---

# 💣 Offline Vulnerability Scanning

### retire.js
- Detect vulnerable JS libraries
- CVE mapping
- Version analysis

### njsscan
- Static JS security scanner
- SAST for JS

Outputs stored under:

```
targets/<domain>/attack/offline/
```

---

# 🧠 Why Vajra?

Because modern bug bounty is:

> 🧠 80% recon  
> ⚡ 20% exploitation  

And JS is where logic, secrets, endpoints & client-side vulns live.

---

# 🎯 Use Case Flow

1. Discovery
2. Download JS
3. Extract everything
4. Hunt secrets
5. Analyze libraries
6. Run offline scanners
7. Profit 💰

---

# 🛡️ Built For

- 🐞 Bug Bounty Hunters
- 🔴 Red Team Operators
- 🕶️ JS-focused Recon
- 💣 Client-side vulnerability research

---

# ⚔️ Philosophy

> Automate the boring.  
> Extract everything.  
> Miss nothing.  

---

# 🧨 Example Workspace

```
targets/target.com/
├── discovery/
├── download/
├── extraction/
├── secret/
├── attack/
```

Everything organized. No chaos. Pure signal.

---

# 👤 Author

Indra ☠️

---

# ⚠️ Disclaimer

This tool is for educational and authorized security testing only.  
You are responsible for your actions.

---

# 🏴 Happy Hunting

> Recon hard.  
> Think deeper.  
> Break smarter.  

⚔️🔥

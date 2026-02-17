#!/usr/bin/env python3

import subprocess
import sys
import os
import platform
import shutil
from pathlib import Path
import venv

# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = (BASE_DIR / "../.tools").resolve()
HOME = Path.home()
LOCAL_BIN = HOME / ".local/bin"

# ==================================================
# CORE UTIL
# ==================================================

def run(cmd, cwd=None, check=True):
    print(f"\n[>] {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and result.returncode != 0:
        print(f"\n[✘] Failed: {cmd}")
        sys.exit(1)
    return result.returncode == 0


def success(msg):
    print(f"[✔] {msg}")


def warn(msg):
    print(f"[!] {msg}")


def exists(bin_name):
    return shutil.which(bin_name) is not None


# ==================================================
# SYSTEM DETECTION
# ==================================================

def detect_os():
    os_name = platform.system()
    success(f"OS: {os_name}")
    return os_name


def detect_shell():
    shell = Path(os.environ.get("SHELL", "")).name
    success(f"Shell: {shell}")
    return shell


def ensure_path(shell):
    LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    export_line = 'export PATH="$HOME/.local/bin:$PATH"'

    if shell == "zsh":
        rc = HOME / ".zshrc"
    elif shell == "bash":
        rc = HOME / ".bashrc"
    else:
        rc = HOME / ".profile"

    if rc.exists():
        if export_line not in rc.read_text():
            with open(rc, "a") as f:
                f.write(f"\n{export_line}\n")
            success(f"PATH updated in {rc.name}")
    else:
        rc.write_text(export_line + "\n")
        success(f"{rc.name} created")


# ==================================================
# DEPENDENCIES
# ==================================================

def check_base_dependencies():
    print("\n====== Checking Base Dependencies ======")
    for tool in ["git", "curl", "pip3"]:
        if not exists(tool):
            print(f"[✘] Missing dependency: {tool}")
            sys.exit(1)
    success("Base dependencies OK")


# ==================================================
# GO
# ==================================================

def ensure_go():
    print("\n====== Checking Go ======")

    if not exists("go"):
        warn("Go not found. Installing...")

        os_name = detect_os()

        if os_name == "Linux":
            run("sudo apt update && sudo apt install -y golang")
        elif os_name == "Darwin":
            run("brew install go")
        else:
            print("Unsupported OS")
            sys.exit(1)

    version = subprocess.check_output("go version", shell=True).decode().strip()
    success(version)


GO_TOOLS = [
    "github.com/BishopFox/jsluice/cmd/jsluice@latest",
    "github.com/eth0izzle/shhgit@latest",
    "github.com/jaeles-project/gospider@latest",
    "github.com/hakluke/hakrawler@latest",
    "github.com/projectdiscovery/katana/cmd/katana@latest",
    "github.com/lc/subjs@latest",
    "github.com/lc/gau/v2/cmd/gau@latest",
    "github.com/003random/getJS/v2@latest",
    "github.com/tomnomnom/waybackurls@latest",
    "github.com/denandz/sourcemapper@latest",
    "github.com/zricethezav/gitleaks/v8@latest",
]


def install_go_tools():
    print("\n====== Installing Go Tools ======")
    for tool in GO_TOOLS:
        run(f"go install {tool}")
    success("Go tools installed")


# ==================================================
# TRUFFLEHOG
# ==================================================

def install_trufflehog():
    print("\n====== Installing TruffleHog ======")

    LOCAL_BIN.mkdir(parents=True, exist_ok=True)

    run(
        "curl -sSfL "
        "https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh "
        f"| sh -s -- -b {LOCAL_BIN}"
    )

    success("TruffleHog installed")


# ==================================================
# NPM
# ==================================================

def setup_npm():
    print("\n====== Configuring NPM ======")

    if not exists("npm"):
        warn("npm not installed")
        return

    npm_dir = HOME / ".npm-global"
    npm_dir.mkdir(exist_ok=True)

    run(f"npm config set prefix '{npm_dir}'")
    run("npm install -g retire")

    success("NPM tools installed")


# ==================================================
# REPOS
# ==================================================

REPOS = {
    "DumpsterDiver": "https://github.com/securing/DumpsterDiver.git",
    "SecretFinder": "https://github.com/m4ll0k/SecretFinder.git",
    "LinkFinder": "https://github.com/GerbenJavado/LinkFinder.git",
}


def clone_repositories():
    print("\n====== Cloning Repositories ======")

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in REPOS.items():
        dest = TOOLS_DIR / name
        if dest.exists():
            success(f"{name} exists")
        else:
            run(f"git clone {url} {dest}")
            success(f"{name} cloned")


# ==================================================
# PYTHON (VENV PER REPO)
# ==================================================

def rewrite_requirements(req_file):
    lines = req_file.read_text().splitlines()
    new_lines = []

    for line in lines:
        if line.strip().startswith("PyYAML==5.4"):
            warn("Rewriting PyYAML 5.4 → >=6.0")
            new_lines.append("PyYAML>=6.0")
        else:
            new_lines.append(line)

    req_file.write_text("\n".join(new_lines))


def setup_repo_venv(repo_path):
    venv_path = repo_path / ".venv"

    if not venv_path.exists():
        venv.create(venv_path, with_pip=True)
        success(f"venv created for {repo_path.name}")

    pip_bin = venv_path / "bin/pip"

    req = repo_path / "requirements.txt"
    if req.exists():
        rewrite_requirements(req)
        run(f"{pip_bin} install --upgrade pip")
        run(f"{pip_bin} install -r {req}")

    if repo_path.name == "LinkFinder":
        run(f"{pip_bin} install .", cwd=repo_path)

    success(f"{repo_path.name} environment ready")


def setup_python_environments():
    print("\n====== Setting up Python Environments ======")

    for repo in REPOS.keys():
        setup_repo_venv(TOOLS_DIR / repo)


# ==================================================
# MAIN
# ==================================================

def main():
    print("\n🔥 ===== VAJRA PRO INSTALLER ===== 🔥")

    os_name = detect_os()
    shell = detect_shell()

    ensure_path(shell)
    check_base_dependencies()
    ensure_go()
    install_go_tools()
    install_trufflehog()
    setup_npm()
    clone_repositories()
    setup_python_environments()

    print("\n🔥 INSTALL COMPLETE 🔥\n")


if __name__ == "__main__":
    main()

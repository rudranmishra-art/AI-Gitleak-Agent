"""
setup.py — AI-Gitleak-Agent Team Setup Script
=============================================
Run this ONCE after cloning the repo:

    python setup.py

What it does:
  1. Checks Python version
  2. Creates a virtual environment (.venv)
  3. Installs all dependencies
  4. Checks gitleaks is installed
  5. Installs the pre-commit hook
  6. Verifies everything works

Works on: Windows, macOS, Linux
"""

import subprocess
import sys
import os
import shutil
import platform

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✅ {msg}{RESET}")
def err(msg):   print(f"  {RED}❌ {msg}{RESET}")
def warn(msg):  print(f"  {YELLOW}⚠  {msg}{RESET}")
def info(msg):  print(f"  {BLUE}ℹ  {msg}{RESET}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")

IS_WINDOWS = platform.system() == "Windows"

# ── Helpers ───────────────────────────────────────────────────────────────────
def run(cmd, check=True, capture=False):
    return subprocess.run(
        cmd, check=check,
        capture_output=capture, text=True
    )

def venv_python():
    """Return path to the venv Python executable."""
    if IS_WINDOWS:
        return os.path.join(".venv", "Scripts", "python.exe")
    return os.path.join(".venv", "bin", "python")

def venv_bin(name):
    """Return path to a binary inside the venv."""
    if IS_WINDOWS:
        return os.path.join(".venv", "Scripts", f"{name}.exe")
    return os.path.join(".venv", "bin", name)

# ── Steps ─────────────────────────────────────────────────────────────────────
def check_python():
    header("Step 1/5 — Checking Python version")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 9):
        err(f"Python 3.9+ required. You have {major}.{minor}.")
        sys.exit(1)
    ok(f"Python {major}.{minor} — OK")


def create_venv():
    header("Step 2/5 — Setting up virtual environment")
    if os.path.isdir(".venv"):
        ok(".venv already exists — skipping creation")
        return
    info("Creating .venv …")
    run([sys.executable, "-m", "venv", ".venv"])
    ok(".venv created")


def install_dependencies():
    header("Step 3/5 — Installing Python dependencies")
    py = venv_python()

    # Upgrade pip silently
    run([py, "-m", "pip", "install", "--upgrade", "pip", "-q"])

    # Install project requirements
    if os.path.isfile("requirements.txt"):
        run([py, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
        ok("Project dependencies installed (rich, pyyaml)")
    else:
        warn("requirements.txt not found — skipping")

    # Install pre-commit
    run([py, "-m", "pip", "install", "pre-commit", "-q"])
    ok("pre-commit installed")


def check_gitleaks():
    header("Step 4/5 — Checking Gitleaks installation")
    path = shutil.which("gitleaks")
    if path:
        result = run(["gitleaks", "version"], capture=True, check=False)
        version = result.stdout.strip() or result.stderr.strip()
        ok(f"Gitleaks found at {path}  ({version})")
        return True
    else:
        err("Gitleaks not found on PATH!")
        print()
        print("  Please install Gitleaks:")
        if IS_WINDOWS:
            print("    winget install gitleaks   (Windows Package Manager)")
            print("    OR download from: https://github.com/gitleaks/gitleaks/releases")
        elif platform.system() == "Darwin":
            print("    brew install gitleaks")
        else:
            print("    Download from: https://github.com/gitleaks/gitleaks/releases")
        print()
        warn("Continuing setup — install Gitleaks and re-run to enable scanning.")
        return False


def install_pre_commit_hook():
    header("Step 5/5 — Installing pre-commit hook")

    # Check .pre-commit-config.yaml exists
    if not os.path.isfile(".pre-commit-config.yaml"):
        err(".pre-commit-config.yaml not found. Is this the right directory?")
        sys.exit(1)

    pre_commit = venv_bin("pre-commit")

    # Check if venv pre-commit exists, fallback to system
    if not os.path.isfile(pre_commit):
        pre_commit = shutil.which("pre-commit")
        if not pre_commit:
            err("pre-commit binary not found even after install. Try re-running setup.")
            sys.exit(1)

    result = run([pre_commit, "install"], capture=True, check=False)
    if result.returncode == 0:
        ok("Pre-commit hook installed at .git/hooks/pre-commit")
    else:
        err(f"Failed to install hook: {result.stderr}")
        sys.exit(1)

    # Run a quick validation
    result = run([pre_commit, "run", "--all-files"], capture=True, check=False)
    if result.returncode in (0, 1):   # 1 = findings, still means hook works
        ok("Hook verified — running correctly")
    else:
        warn(f"Hook validation returned unexpected code {result.returncode}")


def print_summary(gitleaks_ok):
    print(f"\n{'═'*55}")
    print(f"{BOLD}{GREEN}  🎉 Setup Complete!{RESET}")
    print(f"{'═'*55}")
    print()
    print("  Your environment is ready:")
    print(f"  {GREEN}✅{RESET} Virtual environment  → .venv/")
    print(f"  {GREEN}✅{RESET} Dependencies         → rich, pyyaml, pre-commit")
    print(f"  {'✅' if gitleaks_ok else '⚠ '} Gitleaks             → {'installed' if gitleaks_ok else 'MISSING — install manually'}")
    print(f"  {GREEN}✅{RESET} Pre-commit hook      → .git/hooks/pre-commit")
    print()
    print("  Every future commit will be scanned automatically.")
    print()

    activate_cmd = (
        ".venv\\Scripts\\Activate.ps1" if IS_WINDOWS
        else "source .venv/bin/activate"
    )
    print(f"  {BOLD}To activate the virtual environment:{RESET}")
    print(f"    {BLUE}{activate_cmd}{RESET}")
    print()
    print(f"  {BOLD}To enable AI explanations:{RESET}")
    print(f"    {BLUE}set ANTHROPIC_API_KEY=your-key{RESET}  (Windows)")
    print(f"    {BLUE}export ANTHROPIC_API_KEY=your-key{RESET}  (Mac/Linux)")
    print()
    print(f"  {BOLD}To run a manual scan:{RESET}")
    print(f"    {BLUE}python main.py{RESET}")
    print(f"{'═'*55}\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{BOLD}{'═'*55}")
    print("  🔐 AI-Gitleak-Agent Setup")
    print(f"{'═'*55}{RESET}")

    # Verify we're in the right directory
    if not os.path.isfile("main.py") or not os.path.isdir("agent"):
        err("Please run this script from the AI-Gitleak-Agent project root.")
        err("  cd AI-Gitleak-Agent && python setup.py")
        sys.exit(1)

    check_python()
    create_venv()
    install_dependencies()
    gitleaks_ok = check_gitleaks()
    install_pre_commit_hook()
    print_summary(gitleaks_ok)


if __name__ == "__main__":
    main()

import subprocess
import sys
import shutil
import os
from pathlib import Path


def is_uv_installed() -> bool:
    """Check if uv is available in the system path."""
    return shutil.which("uv") is not None


def run():
    # 1. Ensure we are in the project root
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)

    # 2. Check for uv (Mandatory per gemini.md)
    if not is_uv_installed():
        print("❌ Error: 'uv' is not installed.")
        print("Please install it: https://github.com/astral-sh/uv")
        print('Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"')
        print("Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

    # 3. Synchronize environment
    print("🚀 Synchronizing dependencies...")
    try:
        subprocess.run(["uv", "sync"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to synchronize dependencies.")
        sys.exit(1)

    # 4. Forward arguments to main.py
    # This allows: python run.py --cli --limit 10
    args = sys.argv[1:]

    # We use 'uv run' to ensure the correct venv is used
    cmd = ["uv", "run", "python", "main.py"] + args

    print(f"📈 Launching application: {' '.join(cmd)}")
    try:
        # We use a blocking call to keep the process alive
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Application exited with error code {e.returncode}")


if __name__ == "__main__":
    run()

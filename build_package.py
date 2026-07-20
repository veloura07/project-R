"""
build_package.py — Build helper script to compile and package RealityOS as an SDK.
"""

import sys
import subprocess
import os

def run_command(cmd: list):
    print(f"Running: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(res.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error during command execution:\n{e.stderr}", file=sys.stderr)
        raise e

def main():
    print("=== RealityOS SDK Build System ===")
    
    # Check if we are running in the correct directory
    if not os.path.exists("pyproject.toml"):
        print("Error: Run this script from the project root directory.", file=sys.stderr)
        sys.exit(1)
        
    print("\n[Step 1] Verifying build dependencies...")
    try:
        import build
        print(" Found python-build package.")
    except ImportError:
        print(" Python-build package not found. Installing via pip...")
        try:
            run_command([sys.executable, "-m", "pip", "install", "--upgrade", "build"])
        except Exception:
            print("Failed to auto-install build tool. Please run: pip install build", file=sys.stderr)
            sys.exit(1)
            
    print("\n[Step 2] Building RealityOS package (wheel and source distribution)...")
    try:
        run_command([sys.executable, "-m", "build"])
        print("\n=== Build Successful ===")
        print("Packages generated in the 'dist/' folder:")
        for file in os.listdir("dist"):
            print(f" - dist/{file}")
            
        print("\nTo install this package locally in editable/developer mode, run:")
        print(" pip install -e .")
        print("\nTo install the generated distribution package, run:")
        print(" pip install dist/<wheel-name>.whl")
    except Exception as e:
        print(f"\nBuild failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

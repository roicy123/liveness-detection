import subprocess
import sys
import os

if __name__ == "__main__":
    # Provides programmatic execution. Pytest can also be run directly via `pytest -v`.
    root_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir
    
    print(f"Executing pytest suite in {root_dir}...")
    result = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=root_dir, env=env)
    sys.exit(result.returncode)

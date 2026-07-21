import subprocess
import os

env = os.environ.copy()
env["PYTHONPATH"] = r"c:\Users\roicy\.gemini\antigravity\scratch\liveness-detection"

result = subprocess.run(["pytest", "-v"], capture_output=True, text=True, env=env)
with open("test_out.txt", "w", encoding="utf-8") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)

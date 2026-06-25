import subprocess
import sys

print("Installing dependencies...")
result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)

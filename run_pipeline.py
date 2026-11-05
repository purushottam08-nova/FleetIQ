import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

scripts = [
    ROOT / "src" / "generate_data.py",
    ROOT / "src" / "clean_data.py"
]

print("\n================================")
print("       FLEETIQ DATA PIPELINE")
print("================================\n")

for script in scripts:

    print(f"\nRunning: {script.name}")

    subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        check=True
    )

print("\n================================")
print("   PIPELINE EXECUTION SUCCESS")
print("================================")
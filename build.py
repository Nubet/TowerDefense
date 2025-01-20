# This script requires dependencies from requirements.txt

import argparse
import subprocess

files = ["main.py","button.py","world.py","enemy.py","turret.py"]

# Using pycodestyle according to Scripting Languager Course
def lint():
    for file in files:
        subprocess.run(["python", "-m", "pycodestyle", "--max-line-length=120", file])

# Ruff is configured to reformat code according to pycodestyle rules
def fmt():
    config_path = "ruff.toml"
    for file in files:
        subprocess.run(["python", "-m", "ruff", "format", f"--config={config_path}", file])

def main():
    parser = argparse.ArgumentParser(prog="lint")
    subparsers = parser.add_subparsers()
    subparsers.add_parser("lint").set_defaults(func=lint)
    subparsers.add_parser("fmt").set_defaults(func=fmt)
    args = parser.parse_args()

    args.func()


if __name__ == '__main__':
    main()
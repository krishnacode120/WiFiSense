"""Inspect staged files, or all tracked files with --all, without printing secrets."""
from pathlib import PurePosixPath
import re
import subprocess
import sys

args = ["git", "ls-files", "-z"] if "--all" in sys.argv else ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
paths = subprocess.check_output(args).decode().split("\0")
failures = []
for path in filter(None, paths):
    p = PurePosixPath(path)
    forbidden = (p.name.startswith(".env") and p.name != ".env.example") or any(part in {".venv","venv","node_modules","test-results",".tools"} for part in p.parts) or p.suffix in {".db",".sqlite",".sqlite3",".log"} or ".db-" in p.name
    if forbidden:
        failures.append(path + ": forbidden artifact")
        continue
    content = subprocess.check_output(["git", "show", ":" + path])
    patterns = [rb"gh[pousr]_[A-Za-z0-9]{30,}", rb"github_pat_[A-Za-z0-9_]{30,}", rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    if any(re.search(pattern, content) for pattern in patterns):
        failures.append(path + ": potential secret")
if failures:
    print("\n".join(failures))
    sys.exit(1)
print("Repository hygiene passed. Manually review synthetic fixtures and staged changes too.")

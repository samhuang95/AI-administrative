"""Helper script to append assistant-originated entries to the repo `log.md`.

Usage examples:
  # append a short assistant note
  python .\scripts\assistant_append_log.py "Fixed post-commit hook to call repo log_writer.py" --files .git/hooks/post-commit

  # append with an explicit action type
  python .\scripts\assistant_append_log.py "Changed agent name to valid identifier" --action UPDATE --files ai-agent/agent.py

This script imports the project's `log_writer.append_log` function when run from the repo root.
"""
from pathlib import Path
import argparse
import sys

# Ensure repo root is on sys.path so we can import log_writer
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

try:
    from log_writer import append_log
except Exception as e:
    print("Unable to import log_writer from repo root:", e)
    raise


def main() -> None:
    p = argparse.ArgumentParser(description="Append an assistant-originated entry to repo log.md")
    p.add_argument("description", help="Short description for the log entry")
    p.add_argument("--action", default="ASSISTANT", help="Action label, e.g. UPDATE/CREATE/ASSISTANT")
    p.add_argument("--files", help="Comma-separated list of files to attach")
    args = p.parse_args()

    files = [s.strip() for s in args.files.split(",")] if args.files else None
    append_log(args.action, args.description, command=None, files=files)
    print("Appended assistant entry to log.md")


if __name__ == "__main__":
    main()

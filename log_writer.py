"""Simple log writer for repository-level `log.md`.

Usage (from repository root):
  python -m ai_agent.log_writer "Short description" --action UPDATE --command "py -3 script.py" --files ai-agent/foo.py,ai-agent/bar.py

Or import and call append_log(...) from other scripts.
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Iterable, Optional
import argparse
import subprocess


# The log writer lives at the repository root. Use the file's parent as
# the repo root (not parent.parent, which points above the repo).
ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "log.md"


def _now_iso() -> str:
    return datetime.now().isoformat(sep=' ', timespec='seconds')


def append_log(action: str, description: str, command: Optional[str] = None, files: Optional[Iterable[str]] = None) -> None:
    """Append a simple entry to the repo `log.md`.

    Args:
        action: short action type, e.g. CREATE, UPDATE, DELETE, TEST
        description: one-line description of what was done
        command: optional shell/py command executed
        files: optional iterable of file paths changed/created
    """
    files_list = list(files) if files else []
    entry_lines = []
    entry_lines.append(f"- [{_now_iso()}] {action}: {description}")
    if command:
        entry_lines.append(f"  - command: `{command}`")
    if files_list:
        entry_lines.append("  - files:")
        for f in files_list:
            entry_lines.append(f"    - `{f}`")
    entry_lines.append("")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Create file if missing
    if not LOG_PATH.exists():
        LOG_PATH.write_text("# 操作紀錄\n\n")

    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(entry_lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a simple entry to repo log.md")
    parser.add_argument("description", nargs='?', default='(no description)', help="Short description of the action")
    parser.add_argument("--action", default="UPDATE", help="Action type (CREATE/UPDATE/DELETE/TEST)")
    parser.add_argument("--command", help="Command that was run")
    parser.add_argument("--files", help="Comma-separated list of files changed/created")
    parser.add_argument("--from-hook", action="store_true", help="Run as a git hook: auto-detect commit message and files")
    args = parser.parse_args()

    if getattr(args, "from_hook", False):
        # When invoked from a git hook, let Python call git to get the
        # last commit message and changed files (avoids shell-tool
        # portability issues on Windows).
        try:
            commit_msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True).strip()
        except Exception:
            commit_msg = "(unable to read commit message)"

        try:
            files_out = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], text=True)
            files = [s for s in (files_out or "").splitlines() if s]
        except Exception:
            files = None

        append_log("COMMIT", commit_msg.replace("\n", " "), command=f"git commit -m \"{commit_msg}\"", files=files)
        return

    files = [s.strip() for s in args.files.split(",")] if args.files else None
    append_log(args.action, args.description, command=args.command, files=files)


if __name__ == "__main__":
    main()

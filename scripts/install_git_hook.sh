#!/usr/bin/env bash
set -euo pipefail

# Install post-commit git hook (bash)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$REPO_ROOT" ]; then
    REPO_ROOT="."
fi
HOOK_DIR="$REPO_ROOT/.git/hooks"
mkdir -p "$HOOK_DIR"
HOOK_PATH="$HOOK_DIR/post-commit"

cat > "$HOOK_PATH" <<'HOOK'
#!/usr/bin/env bash
set -e

# Simple post-commit hook that delegates work to Python.
# Python will call git itself to obtain the last commit message and changed files.

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$REPO_ROOT" ]; then
    REPO_ROOT="."
fi

if command -v py >/dev/null 2>&1; then
    PYCMD="py -3"
elif command -v python3 >/dev/null 2>&1; then
    PYCMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYCMD="python"
else
    echo "Python not found in PATH; skipping log append." >&2
    exit 0
fi

LOG_WRITER="$REPO_ROOT/log_writer.py"
if [ -f "$LOG_WRITER" ]; then
    exec $PYCMD "$LOG_WRITER" --from-hook
else
    echo "log_writer.py not found at $LOG_WRITER; skipping." >&2
    exit 0
fi
HOOK

chmod +x "$HOOK_PATH" || true
echo "Installed post-commit hook at $HOOK_PATH"

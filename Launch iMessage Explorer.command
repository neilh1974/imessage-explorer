#!/bin/bash
# double-click to launch (right-click > Open the first time if blocked)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/imessage_explorer.py"

if ! python3 -c "import flask" 2>/dev/null; then
    echo "installing Flask..."
    pip3 install flask --break-system-packages -q
fi

echo "starting at http://localhost:5001  (Ctrl+C to stop)"
(sleep 2 && open "http://localhost:5001") &
python3 "$APP"

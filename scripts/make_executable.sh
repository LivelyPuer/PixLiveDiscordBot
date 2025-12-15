#!/bin/bash
# Сделать все скрипты исполняемыми

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

chmod +x "$SCRIPT_DIR/setup.sh"
chmod +x "$SCRIPT_DIR/update.sh"
chmod +x "$SCRIPT_DIR/run.sh"

echo "✅ Все скрипты сделаны исполняемыми"

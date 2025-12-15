#!/bin/bash
set -e

# Простой скрипт для локального запуска в режиме разработки
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🚀 PixLive Bot - Local Development"
echo "Project: $PROJECT_DIR"
echo ""

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

# Создаём виртуальное окружение если нужно
if [ ! -d "venv" ]; then
    echo "📦 Создаём виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем окружение
source venv/bin/activate

# Обновляем зависимости
echo "📥 Обновляем зависимости..."
pip install -q -r requirements.txt

# Запускаем проверку конфига
echo ""
python3 scripts/check_config.py

# Запускаем бота
echo ""
echo "🎬 Запускаем бота..."
echo "Нажмите Ctrl+C для остановки"
echo ""

python3 main.py



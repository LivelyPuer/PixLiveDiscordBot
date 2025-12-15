#!/bin/bash
#
# PixLive Bot - Быстрый запуск локально
# Использование: bash scripts/run.sh
#

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Определить директорию проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"

cd "$INSTALL_DIR" || log_error "Не удалось перейти в директорию $INSTALL_DIR"

# Проверить .env
if [ ! -f ".env" ]; then
    log_warning ".env файл не найден"
    if [ -f ".env.example" ]; then
        log_info "Создаю .env из .env.example"
        cp .env.example .env
        log_warning "⚠️  Отредактируй .env:"
        log_warning "   nano .env"
        exit 1
    fi
fi

# Проверить виртуальное окружение
if [ ! -d "venv" ]; then
    log_info "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активировать venv
log_info "Активация виртуального окружения..."
source venv/bin/activate

# Установить зависимости если нужно
if ! python3 -c "import discord" 2>/dev/null; then
    log_info "Установка зависимостей..."
    pip install -r requirements.txt -q
fi

# Проверить конфиг
log_info "Проверка конфигурации..."
python3 check_config.py || exit 1

echo ""
log_success "Все готово к запуску!"
echo ""
echo "Запускаю PixLive Bot..."
echo "(Нажми Ctrl+C для остановки)"
echo ""

# Запустить бота
python3 main.py

#!/bin/bash
#
# PixLive Bot - Быстрое обновление и перезагрузка
# Использование: bash scripts/update.sh
# Не требует root прав
#

set -e

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Определить директорию проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"

cd "$INSTALL_DIR" || log_error "Не удалось перейти в директорию $INSTALL_DIR"

log_info "Директория проекта: $INSTALL_DIR"

# Проверить что мы в правильной директории
if [ ! -f "main.py" ]; then
    log_error "main.py не найден. Убедись что запускаешь скрипт правильно"
fi

echo ""
log_info "Обновление кода..."

# Получить текущую ветку
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Текущая ветка: $CURRENT_BRANCH"

# Обновить код
git fetch origin
git reset --hard "origin/${CURRENT_BRANCH}" 2>/dev/null || git reset --hard origin/main

log_success "Код обновлен"

# Активировать виртуальное окружение
if [ ! -d "venv" ]; then
    log_error "Виртуальное окружение не найдено. Запусти: python3 -m venv venv"
fi

source venv/bin/activate || log_error "Не удалось активировать venv"

log_info "Обновление зависимостей Python..."
pip install -r requirements.txt -q

log_success "Зависимости обновлены"

# Проверить конфигурацию
echo ""
log_info "Проверка конфигурации..."

if python3 check_config.py > /dev/null 2>&1; then
    log_success "Конфигурация валидна"
else
    log_warning "Может быть ошибка в конфигурации"
    log_info "Запусти: python3 check_config.py"
fi

# Запустить тесты
echo ""
read -p "Запустить тесты? (y/n): " run_tests

if [[ "$run_tests" == "y" ]]; then
    log_info "Запуск тестов..."
    echo ""
    python3 tests/test_deviantart.py
fi

# Перезагрузить сервис
echo ""
if [ -f "/etc/systemd/system/pixlive.service" ]; then
    log_info "Перезагрузка systemd сервиса..."
    sudo systemctl restart pixlive
    
    sleep 2
    if sudo systemctl is-active --quiet pixlive; then
        log_success "Сервис перезагружен"
        log_info "Смотреть логи: sudo journalctl -u pixlive -f"
    else
        log_warning "Не удалось запустить сервис"
        log_info "Проверь: sudo systemctl status pixlive"
    fi
else
    log_warning "Systemd сервис не найден"
    log_info "Если используешь screen: подсоедись и перезагрузи вручную"
fi

echo ""
log_success "Обновление завершено!"
echo ""

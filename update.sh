#!/bin/bash

################################################################################
# PixLive Discord Bot - Update Script
# 
# Простой скрипт для обновления кода и зависимостей
# Использование: bash update.sh
#
################################################################################

set -euo pipefail

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_title() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n${BLUE}$1${NC}\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

BOT_HOME="/opt/PixLiveDiscordBot"
BOT_VENV="${BOT_HOME}/venv"
REPO_URL="https://github.com/LivelyPuer/PixLiveDiscordBot.git"

# Проверка прав доступа
if [[ $EUID -ne 0 ]]; then
    log_error "Требуются права root"
    echo "Используй: sudo bash update.sh"
    exit 1
fi

log_title "ОБНОВЛЕНИЕ PIXLIVE DISCORD BOT"

# Обновление репо
log_info "Обновляю код из GitHub..."
cd "$BOT_HOME"
git fetch origin
git reset --hard origin/HEAD
log_info "Код обновлен"

# Обновление зависимостей
log_info "Обновляю зависимости Python..."
"$BOT_VENV/bin/pip" install --quiet --upgrade -r "$BOT_HOME/requirements.txt"
log_info "Зависимости обновлены"

# Перезагрузка
log_info "Перезагружаю сервис..."
systemctl restart pixlive
sleep 2

if systemctl is-active --quiet pixlive; then
    log_title "✓ ОБНОВЛЕНИЕ УСПЕШНО"
    echo "Сервис перезагружен и работает"
    echo "Логи: sudo journalctl -u pixlive -f"
else
    log_error "Ошибка при запуске сервиса"
    journalctl -u pixlive -n 20
    exit 1
fi

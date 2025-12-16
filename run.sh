#!/bin/bash

################################################################################
# PixLive Discord Bot - Quick Run Script
# 
# Быстрый запуск локально с автоматической настройкой
# Использование: bash run.sh
#
################################################################################

set -euo pipefail

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_title() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n${BLUE}$1${NC}\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

log_title "PixLive Discord Bot - Запуск"

# 1. Проверка .env
if [[ ! -f "${SCRIPT_DIR}/.env" ]]; then
    log_error ".env не найден"
    if [[ -f "${SCRIPT_DIR}/.env.example" ]]; then
        log_info "Создаю .env из примера..."
        cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
        log_info "Отредактируй .env перед запуском!"
        
        if command -v nano &> /dev/null; then
            read -p "Отредактировать .env сейчас? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                nano "${SCRIPT_DIR}/.env"
            fi
        fi
    else
        log_error "Не найден .env.example"
        exit 1
    fi
fi

# 2. Создание виртуального окружения
if [[ ! -d "$VENV_DIR" ]]; then
    log_info "Создаю виртуальное окружение..."
    python3 -m venv "$VENV_DIR"
    log_info "venv создан"
fi

# 3. Обновление pip
log_info "Обновляю pip..."
"$PIP" install --quiet --upgrade pip setuptools wheel

# 4. Установка зависимостей
log_info "Устанавливаю зависимости..."
"$PIP" install --quiet -r "${SCRIPT_DIR}/requirements.txt"

# 5. Запуск
log_title "Запуск PixLive Discord Bot..."
echo -e "${BLUE}Нажми Ctrl+C для остановки${NC}\n"

"$PYTHON" "${SCRIPT_DIR}/main.py"

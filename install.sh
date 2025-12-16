#!/bin/bash

################################################################################
# PixLive Discord Bot - One Command Deploy
# 
# Полное развертывание с одной команды
# 
# Использование на сервере:
#   curl -fsSL https://raw.githubusercontent.com/LivelyPuer/PixLiveDiscordBot/main/install.sh | sudo bash
#
# Или локально:
#   sudo bash install.sh
#
################################################################################

set -euo pipefail

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_success() { echo -e "${GREEN}✓ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_title() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n${BLUE}$1${NC}\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

# Конфигурация
REPO_URL="https://github.com/LivelyPuer/PixLiveDiscordBot.git"
BOT_USER="pixlive"
BOT_HOME="/opt/PixLiveDiscordBot"
BOT_VENV="${BOT_HOME}/venv"
SYSTEMD_SERVICE="pixlive"
SYSTEMD_PATH="/etc/systemd/system/${SYSTEMD_SERVICE}.service"

# Проверка root
if [[ $EUID -ne 0 ]]; then
    log_error "Требуются права root. Используй: sudo bash install.sh"
    exit 1
fi

log_title "PIXLIVE DISCORD BOT - РАЗВЕРТЫВАНИЕ"
echo "Репо: $REPO_URL"
echo "Домашняя папка: $BOT_HOME"
echo ""

# 1. Определение OS и установка зависимостей
log_info "Определяю ОС..."
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$ID
else
    log_error "Не удается определить ОС"
    exit 1
fi

log_info "Обнаружена ОС: $OS"
log_info "Обновляю пакеты и устанавливаю зависимости..."

case $OS in
    ubuntu|debian)
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
            python3 python3-pip python3-venv \
            git curl wget \
            build-essential libssl-dev \
            > /dev/null 2>&1
        ;;
    centos|rhel|fedora)
        yum install -y -q \
            python3 python3-pip \
            git curl wget \
            gcc openssl-devel \
            > /dev/null 2>&1
        ;;
    alpine)
        apk add --no-cache --quiet \
            python3 py3-pip \
            git curl wget \
            build-base openssl-dev
        ;;
    *)
        log_warning "Неизвестная ОС: $OS. Убедись что установлены Python3, git, build-essential"
        ;;
esac

log_success "Зависимости установлены"

# 2. Создание пользователя
log_info "Создаю пользователя $BOT_USER..."
if ! id "$BOT_USER" &>/dev/null; then
    useradd -m -s /bin/bash -d "$BOT_HOME" "$BOT_USER" || true
    log_success "Пользователь создан"
else
    log_info "Пользователь уже существует"
fi

# 3. Клонирование репо
log_info "Клонирую репозиторий..."
if [[ ! -d "$BOT_HOME" ]]; then
    mkdir -p "$(dirname "$BOT_HOME")"
    git clone "$REPO_URL" "$BOT_HOME" > /dev/null 2>&1
    log_success "Репозиторий клонирован"
else
    log_info "Обновляю существующий репозиторий..."
    cd "$BOT_HOME"
    git fetch origin > /dev/null 2>&1
    git reset --hard origin/HEAD > /dev/null 2>&1
    log_success "Репозиторий обновлен"
fi

# 4. Настройка Python окружения
log_info "Создаю виртуальное окружение..."
cd "$BOT_HOME"
python3 -m venv "$BOT_VENV"

log_info "Обновляю pip..."
"$BOT_VENV/bin/pip" install --quiet --upgrade pip setuptools wheel

log_info "Устанавливаю зависимости..."
"$BOT_VENV/bin/pip" install --quiet -r "$BOT_HOME/requirements.txt"

log_success "Python окружение готово"

# 5. Настройка прав доступа
log_info "Устанавливаю права доступа..."
chown -R "$BOT_USER:$BOT_USER" "$BOT_HOME"
chmod 755 "$BOT_HOME"

# 6. Создание systemd сервиса
log_info "Создаю systemd сервис..."
cat > "$SYSTEMD_PATH" << 'EOF'
[Unit]
Description=PixLive Discord Bot
After=network.target
Documentation=https://github.com/LivelyPuer/PixLiveDiscordBot

[Service]
Type=simple
User=pixlive
WorkingDirectory=/opt/PixLiveDiscordBot
ExecStart=/opt/PixLiveDiscordBot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pixlive
Environment="PYTHONUNBUFFERED=1"

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$SYSTEMD_PATH"
systemctl daemon-reload
log_success "Systemd сервис создан"

# 7. Включение автозапуска
log_info "Включаю автозапуск при старте системы..."
systemctl enable "$SYSTEMD_SERVICE" > /dev/null 2>&1
log_success "Автозапуск включен"

# 8. Проверка .env
if [[ ! -f "$BOT_HOME/.env" ]]; then
    if [[ -f "$BOT_HOME/.env.example" ]]; then
        log_warning ".env не найден"
        cp "$BOT_HOME/.env.example" "$BOT_HOME/.env"
        chown "$BOT_USER:$BOT_USER" "$BOT_HOME/.env"
        chmod 600 "$BOT_HOME/.env"
        log_info "Создан .env из .env.example"
        log_warning "ВАЖНО! Отредактируй .env с необходимыми токенами:"
        log_info "  nano $BOT_HOME/.env"
    fi
else
    log_info ".env уже существует"
fi

# 9. Запуск сервиса
log_info "Запускаю сервис..."
systemctl start "$SYSTEMD_SERVICE"
sleep 2

if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
    log_success "Сервис запущен успешно"
else
    log_error "Ошибка при запуске сервиса"
    journalctl -u "$SYSTEMD_SERVICE" -n 20
    exit 1
fi

# Финальная информация
log_title "✓ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО"

echo -e "
${GREEN}Сервис успешно установлен и запущен!${NC}

${BLUE}Основные команды:${NC}

  ${YELLOW}Управление:${NC}
    sudo systemctl start $SYSTEMD_SERVICE    # Запустить
    sudo systemctl stop $SYSTEMD_SERVICE     # Остановить
    sudo systemctl restart $SYSTEMD_SERVICE  # Перезагрузить
    sudo systemctl status $SYSTEMD_SERVICE   # Статус

  ${YELLOW}Логи и информация:${NC}
    sudo journalctl -u $SYSTEMD_SERVICE -f        # Живые логи
    sudo journalctl -u $SYSTEMD_SERVICE -n 100    # Последние 100 строк
    sudo systemctl is-active $SYSTEMD_SERVICE     # Активен ли?

  ${YELLOW}Обновление:${NC}
    cd $BOT_HOME
    sudo git pull
    sudo systemctl restart $SYSTEMD_SERVICE

  ${YELLOW}Конфигурация:${NC}
    nano $BOT_HOME/.env           # Отредактировать .env
    cat $BOT_HOME/README.md       # Документация

${BLUE}Требуемые переменные в .env:${NC}
  - DISCORD_TOKEN
  - DISCORD_CHANNEL_ID
  - TG_BOT_TOKEN
  - TG_ADMIN_PASSWORD
  - DEVIANTART_CLIENT_ID
  - DEVIANTART_CLIENT_SECRET
  - DEVIANTART_USERNAMES

${BLUE}Дополнительно:${NC}
  Сервис настроен на автоматический запуск при перезагрузке сервера
  Если сервис упадет, он автоматически перезагрузится
"

#!/bin/bash

################################################################################
# PixLive Discord Bot - Deployment Script
# 
# Единый скрипт для полной установки, обновления и управления ботом
# 
# Использование:
#   sudo bash deploy.sh              # Интерактивное меню
#   sudo bash deploy.sh install      # Полная установка
#   sudo bash deploy.sh update       # Обновление с GitHub
#   sudo bash deploy.sh start        # Запустить сервис
#   sudo bash deploy.sh stop         # Остановить сервис
#   sudo bash deploy.sh status       # Статус сервиса
#   sudo bash deploy.sh logs         # Показать логи
#   sudo bash deploy.sh restart      # Перезагрузить сервис
#
################################################################################

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
REPO_URL="https://github.com/LivelyPuer/PixLiveDiscordBot.git"
BOT_USER="pixlive"
BOT_HOME="/opt/PixLiveDiscordBot"
BOT_VENV="${BOT_HOME}/venv"
SYSTEMD_SERVICE="pixlive"
SYSTEMD_PATH="/etc/systemd/system/${SYSTEMD_SERVICE}.service"

# Функции вывода
log_info() {
    echo -e "${GREEN}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_title() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен быть запущен с правами root (используй sudo)"
        exit 1
    fi
}

# Определение OS и установка зависимостей
install_dependencies() {
    log_title "Установка системных зависимостей"
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
    else
        log_error "Не удается определить OS"
        exit 1
    fi

    case $OS in
        ubuntu|debian)
            log_info "Обнаружен Debian/Ubuntu"
            apt-get update -qq
            apt-get install -y -qq \
                python3 python3-pip python3-venv \
                git curl wget \
                build-essential libssl-dev \
                > /dev/null 2>&1
            ;;
        centos|rhel|fedora)
            log_info "Обнаружен RedHat/CentOS"
            yum install -y -q \
                python3 python3-pip \
                git curl wget \
                gcc openssl-devel \
                > /dev/null 2>&1
            ;;
        alpine)
            log_info "Обнаружен Alpine"
            apk add --no-cache \
                python3 py3-pip \
                git curl wget \
                build-base openssl-dev
            ;;
        *)
            log_warning "Неизвестный OS: $OS"
            log_info "Убедись что установлены: Python 3, git, build-essential"
            ;;
    esac

    log_success "Системные зависимости установлены"
}

# Создание пользователя для бота
create_bot_user() {
    log_title "Настройка пользователя $BOT_USER"
    
    if ! id "$BOT_USER" &>/dev/null; then
        log_info "Создание пользователя $BOT_USER..."
        useradd -m -s /bin/bash -d "$BOT_HOME" "$BOT_USER" || true
        log_success "Пользователь $BOT_USER создан"
    else
        log_info "Пользователь $BOT_USER уже существует"
    fi
}

# Клонирование или обновление репозитория
setup_repository() {
    log_title "Настройка репозитория"
    
    if [[ ! -d "$BOT_HOME" ]]; then
        log_info "Клонирование репозитория..."
        mkdir -p "$(dirname "$BOT_HOME")"
        git clone "$REPO_URL" "$BOT_HOME"
        log_success "Репозиторий клонирован"
    else
        log_info "Репозиторий уже существует, обновляю..."
        cd "$BOT_HOME"
        git fetch origin
        git reset --hard origin/HEAD
        log_success "Репозиторий обновлен"
    fi

    # Установка прав доступа
    chown -R "$BOT_USER:$BOT_USER" "$BOT_HOME"
    chmod 755 "$BOT_HOME"
}

# Создание виртуального окружения и установка зависимостей
setup_python_env() {
    log_title "Настройка Python окружения"
    
    # Создание venv если не существует
    if [[ ! -d "$BOT_VENV" ]]; then
        log_info "Создание виртуального окружения..."
        cd "$BOT_HOME"
        python3 -m venv "$BOT_VENV"
        log_success "Виртуальное окружение создано"
    fi

    # Обновление pip
    log_info "Обновление pip..."
    "$BOT_VENV/bin/pip" install --quiet --upgrade pip setuptools wheel

    # Установка зависимостей
    log_info "Установка зависимостей Python..."
    "$BOT_VENV/bin/pip" install --quiet -r "$BOT_HOME/requirements.txt"
    log_success "Зависимости Python установлены"

    # Установка прав доступа
    chown -R "$BOT_USER:$BOT_USER" "$BOT_VENV"
}

# Создание или обновление .env файла
setup_env_file() {
    log_title "Проверка конфигурации"
    
    if [[ -f "$BOT_HOME/.env" ]]; then
        log_info ".env уже существует"
        read -p "Хочешь отредактировать .env? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v nano &> /dev/null; then
                sudo -u "$BOT_USER" nano "$BOT_HOME/.env"
            elif command -v vi &> /dev/null; then
                sudo -u "$BOT_USER" vi "$BOT_HOME/.env"
            else
                log_warning "Не найден текстовый редактор (nano/vi)"
            fi
        fi
    else
        log_warning ".env файл не найден"
        if [[ -f "$BOT_HOME/.env.example" ]]; then
            log_info "Создаю .env из примера..."
            cp "$BOT_HOME/.env.example" "$BOT_HOME/.env"
            log_info "Отредактируй .env с нужными токенами:"
            log_info "  nano $BOT_HOME/.env"
            log_warning "ВАЖНО: Установи необходимые токены перед запуском!"
        fi
    fi

    chown "$BOT_USER:$BOT_USER" "$BOT_HOME/.env"
    chmod 600 "$BOT_HOME/.env"
}

# Создание systemd сервиса
create_systemd_service() {
    log_title "Создание systemd сервиса"
    
    log_info "Создаю файл сервиса: $SYSTEMD_PATH"
    
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
}

# Запуск сервиса при старте системы
enable_autostart() {
    log_title "Включение автозапуска"
    
    systemctl enable "$SYSTEMD_SERVICE"
    log_success "Автозапуск включен (при перезагрузке сервера бот запустится автоматически)"
}

# Запуск сервиса
start_service() {
    log_title "Запуск сервиса"
    
    systemctl start "$SYSTEMD_SERVICE"
    sleep 2
    
    if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
        log_success "Сервис успешно запущен"
        return 0
    else
        log_error "Ошибка при запуске сервиса"
        journalctl -u "$SYSTEMD_SERVICE" -n 20
        return 1
    fi
}

# Остановка сервиса
stop_service() {
    log_title "Остановка сервиса"
    systemctl stop "$SYSTEMD_SERVICE"
    log_success "Сервис остановлен"
}

# Перезагрузка сервиса
restart_service() {
    log_title "Перезагрузка сервиса"
    systemctl restart "$SYSTEMD_SERVICE"
    sleep 2
    
    if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
        log_success "Сервис успешно перезагружен"
    else
        log_error "Ошибка при перезагрузке сервиса"
    fi
}

# Показ статуса
show_status() {
    log_title "Статус сервиса"
    
    echo "Сервис: $SYSTEMD_SERVICE"
    echo ""
    
    if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
        log_success "Сервис запущен"
    else
        log_error "Сервис остановлен"
    fi
    
    echo ""
    echo "Информация systemd:"
    systemctl status "$SYSTEMD_SERVICE" --no-pager || true
}

# Показ логов
show_logs() {
    log_title "Логи сервиса (последние 50 строк, нажми Ctrl+C для выхода)"
    echo ""
    journalctl -u "$SYSTEMD_SERVICE" -n 50 -f
}

# Полная установка
full_install() {
    check_root
    log_title "ПОЛНАЯ УСТАНОВКА PixLive Discord Bot"
    
    install_dependencies
    create_bot_user
    setup_repository
    setup_python_env
    setup_env_file
    create_systemd_service
    enable_autostart
    start_service
    
    log_title "✓ УСТАНОВКА ЗАВЕРШЕНА"
    echo -e "
${GREEN}Что дальше:${NC}

1. Отредактируй конфигурацию если требуется:
   ${BLUE}nano $BOT_HOME/.env${NC}

2. Проверь статус:
   ${BLUE}sudo systemctl status $SYSTEMD_SERVICE${NC}

3. Смотри логи:
   ${BLUE}sudo journalctl -u $SYSTEMD_SERVICE -f${NC}

4. Управление:
   ${BLUE}sudo bash $BOT_HOME/deploy.sh restart  # Перезагрузить${NC}
   ${BLUE}sudo bash $BOT_HOME/deploy.sh stop     # Остановить${NC}
   ${BLUE}sudo bash $BOT_HOME/deploy.sh start    # Запустить${NC}

5. Обновление кода и зависимостей:
   ${BLUE}sudo bash $BOT_HOME/deploy.sh update${NC}
"
}

# Обновление кода
update() {
    check_root
    log_title "ОБНОВЛЕНИЕ PixLive Discord Bot"
    
    log_info "Текущее местоположение: $BOT_HOME"
    
    # Обновление кода
    setup_repository
    
    # Обновление зависимостей
    setup_python_env
    
    # Перезагрузка сервиса
    log_info "Перезагружаю сервис..."
    restart_service
    
    log_title "✓ ОБНОВЛЕНИЕ ЗАВЕРШЕНО"
    echo -e "
${GREEN}Бот обновлен и перезагружен.${NC}
Проверь логи: ${BLUE}sudo journalctl -u $SYSTEMD_SERVICE -f${NC}
"
}

# Интерактивное меню
show_menu() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════╗"
    echo "║     PixLive Discord Bot - Управление              ║"
    echo "╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1) 📥 Полная установка (новая инсталляция)"
    echo "2) 🔄 Обновить код и перезагрузить"
    echo "3) ▶️  Запустить сервис"
    echo "4) ⏹️  Остановить сервис"
    echo "5) 🔁 Перезагрузить сервис"
    echo "6) ℹ️  Показать статус"
    echo "7) 📋 Показать логи"
    echo "8) 🚪 Выход"
    echo ""
    read -p "Выбери опцию (1-8): " choice
}

# Главная функция
main() {
    # Если передан аргумент, используй его как команду
    if [[ $# -gt 0 ]]; then
        case "$1" in
            install)
                full_install
                ;;
            update)
                update
                ;;
            start)
                check_root
                start_service
                ;;
            stop)
                check_root
                stop_service
                ;;
            restart)
                check_root
                restart_service
                ;;
            status)
                check_root
                show_status
                ;;
            logs)
                check_root
                show_logs
                ;;
            *)
                log_error "Неизвестная команда: $1"
                echo "Доступные команды: install, update, start, stop, restart, status, logs"
                exit 1
                ;;
        esac
    else
        # Интерактивное меню
        check_root
        while true; do
            show_menu
            case $choice in
                1) full_install ;;
                2) update ;;
                3) start_service ;;
                4) stop_service ;;
                5) restart_service ;;
                6) show_status ;;
                7) show_logs ;;
                8) log_info "До встречи!"; exit 0 ;;
                *) log_error "Неверный выбор" ;;
            esac
            read -p "Нажми Enter для продолжения..." -r
        done
    fi
}

# Запуск скрипта
main "$@"

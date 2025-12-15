#!/bin/bash
#
# PixLive Discord Bot - Автоматическое развертывание и настройка
# Использование: sudo bash scripts/setup.sh
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Переменные
REPO_URL="https://github.com/LivelyPuer/PixLiveDiscordBot.git"
INSTALL_DIR="/opt/PixLiveDiscordBot"
SERVICE_NAME="pixlive"
SERVICE_USER="pixlive"
PYTHON_MIN_VERSION="3.8"

# Функции логирования
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

# Проверка что скрипт запущен от root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен запускаться от root"
    fi
}

# Проверка OS
check_os() {
    log_info "Проверка операционной системы..."
    
    if [[ ! -f /etc/os-release ]]; then
        log_error "Не удалось определить OS"
    fi
    
    . /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        log_warning "Скрипт протестирован на Ubuntu/Debian. Может быть несовместимость"
    fi
    
    log_success "OS: $ID $VERSION_ID"
}

# Проверка Python версии
check_python() {
    log_info "Проверка Python..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не установлен"
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python версия: $PYTHON_VERSION"
}

# Установка зависимостей системы
install_dependencies() {
    log_info "Установка системных зависимостей..."
    
    apt-get update -qq || log_error "Не удалось обновить пакеты"
    
    # Установить необходимые пакеты
    apt-get install -y -qq \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        vim \
        2>&1 | grep -v "^Get:" | grep -v "^Hit:" || true
    
    log_success "Системные зависимости установлены"
}

# Создание пользователя для бота
create_bot_user() {
    log_info "Проверка пользователя $SERVICE_USER..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        log_info "Создание пользователя $SERVICE_USER..."
        useradd -r -s /bin/bash -d "$INSTALL_DIR" "$SERVICE_USER"
        log_success "Пользователь создан"
    else
        log_success "Пользователь $SERVICE_USER уже существует"
    fi
}

# Клонирование/обновление репозитория
setup_repository() {
    log_info "Настройка репозитория..."
    
    if [ -d "$INSTALL_DIR" ]; then
        log_info "Директория $INSTALL_DIR существует, обновляю код..."
        cd "$INSTALL_DIR"
        git fetch origin
        git reset --hard origin/main 2>/dev/null || git reset --hard origin/master
        log_success "Код обновлен"
    else
        log_info "Клонирование репозитория..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        log_success "Репозиторий клонирован"
    fi
    
    # Установить правильные права
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
}

# Создание виртуального окружения
setup_venv() {
    log_info "Создание виртуального окружения..."
    
    cd "$INSTALL_DIR"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Виртуальное окружение создано"
    fi
    
    # Активировать и обновить pip
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel -q
    
    log_success "Pip обновлен"
}

# Установка зависимостей Python
install_python_deps() {
    log_info "Установка зависимостей Python..."
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
        log_success "Зависимости Python установлены"
    else
        log_error "requirements.txt не найден"
    fi
}

# Проверка .env файла
setup_env() {
    log_info "Проверка конфигурации..."
    
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        if [ -f "$INSTALL_DIR/.env.example" ]; then
            log_warning ".env файл не найден!"
            log_info "Создаю .env из .env.example..."
            cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
            
            log_warning "⚠️  ВНИМАНИЕ! Отредактируй .env файл:"
            log_warning "   nano $INSTALL_DIR/.env"
            log_warning ""
            log_warning "Необходимо заполнить:"
            log_warning "   - DISCORD_TOKEN"
            log_warning "   - DISCORD_CHANNEL_ID"
            log_warning "   - DEVIANTART_CLIENT_ID"
            log_warning "   - DEVIANTART_CLIENT_SECRET"
            log_warning "   - DEVIANTART_USERNAMES"
            log_warning "   - TG_BOT_TOKEN"
            log_warning "   - TG_ADMIN_PASSWORD"
            
            return 1
        else
            log_error ".env и .env.example не найдены"
        fi
    else
        log_success ".env файл найден"
    fi
    
    # Установить правильные права на .env
    chmod 600 "$INSTALL_DIR/.env"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
    
    return 0
}

# Создание systemd сервиса
create_systemd_service() {
    log_info "Создание systemd сервиса..."
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=PixLive Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python main.py

# Автоматический перезапуск при падении
Restart=always
RestartSec=10

# Ограничения ресурсов
MemoryMax=512M
CPUQuota=50%

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pixlive

# Таймауты
StartLimitInterval=600
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
EOF

    chmod 644 "/etc/systemd/system/${SERVICE_NAME}.service"
    
    log_success "Systemd сервис создан"
}

# Перезагрузка systemd
reload_systemd() {
    log_info "Перезагрузка systemd..."
    
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" || log_warning "Не удалось включить автозагрузку"
    
    log_success "Systemd перезагружен"
}

# Запуск бота
start_bot() {
    log_info "Запуск бота..."
    
    systemctl restart "$SERVICE_NAME"
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Бот запущен"
    else
        log_warning "Не удалось запустить бота"
        log_info "Проверь логи: systemctl status $SERVICE_NAME"
        return 1
    fi
}

# Проверка конфигурации
verify_setup() {
    log_info "Проверка конфигурации..."
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    if python3 check_config.py > /dev/null 2>&1; then
        log_success "Конфигурация валидна"
    else
        log_warning "Конфигурация может содержать ошибки"
        log_info "Запусти: python check_config.py"
    fi
}

# Вывод информации о том как смотреть логи
show_info() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✅ УСТАНОВКА ЗАВЕРШЕНА${NC}"
    echo "=========================================="
    echo ""
    echo "📝 Полезные команды:"
    echo ""
    echo "  Статус бота:"
    echo "    systemctl status $SERVICE_NAME"
    echo ""
    echo "  Просмотр логов (последние 50 строк):"
    echo "    journalctl -u $SERVICE_NAME -n 50"
    echo ""
    echo "  Просмотр логов (в реальном времени):"
    echo "    journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "  Перезагрузить бота:"
    echo "    systemctl restart $SERVICE_NAME"
    echo ""
    echo "  Остановить бота:"
    echo "    systemctl stop $SERVICE_NAME"
    echo ""
    echo "  Запустить тесты:"
    echo "    cd $INSTALL_DIR && source venv/bin/activate"
    echo "    python tests/test_deviantart.py"
    echo "    python tests/test_integration.py"
    echo ""
    echo "📁 Директория проекта: $INSTALL_DIR"
    echo "👤 Пользователь: $SERVICE_USER"
    echo "📋 Конфиг: $INSTALL_DIR/.env"
    echo "📊 Логи: /var/log/journal/ (systemd)"
    echo ""
    echo "=========================================="
    echo ""
}

# Меню выбора действия
show_menu() {
    echo ""
    echo "=========================================="
    echo "    PixLive Bot - Автоматическая установка"
    echo "=========================================="
    echo ""
    echo "Выбери действие:"
    echo "  1) Полная установка (новая инсталляция)"
    echo "  2) Обновить код и перезагрузить"
    echo "  3) Только обновить зависимости Python"
    echo "  4) Показать статус"
    echo "  5) Показать логи"
    echo "  6) Выход"
    echo ""
    read -p "Выбор (1-6): " choice
}

# Обновление кода
update_code() {
    log_info "Обновление кода..."
    
    cd "$INSTALL_DIR"
    git fetch origin
    git reset --hard origin/main 2>/dev/null || git reset --hard origin/master
    
    log_success "Код обновлен"
    
    # Обновить зависимости
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    log_success "Зависимости обновлены"
    
    # Перезагрузить сервис
    systemctl restart "$SERVICE_NAME"
    log_success "Сервис перезагружен"
}

# Показать статус
show_status() {
    echo ""
    systemctl status "$SERVICE_NAME"
    echo ""
}

# Показать логи
show_logs() {
    echo ""
    echo "Показываю последние 50 строк логов (Ctrl+C для выхода):"
    echo ""
    journalctl -u "$SERVICE_NAME" -n 50 --no-pager
    echo ""
    read -p "Показать логи в реальном времени? (y/n): " realtime
    if [[ "$realtime" == "y" ]]; then
        journalctl -u "$SERVICE_NAME" -f
    fi
}

# Главная функция
main() {
    check_root
    
    while true; do
        show_menu
        
        case $choice in
            1)
                echo ""
                log_info "Начинаю полную установку..."
                echo ""
                
                check_os
                check_python
                install_dependencies
                create_bot_user
                setup_repository
                setup_venv
                install_python_deps
                
                if setup_env; then
                    create_systemd_service
                    reload_systemd
                    verify_setup
                    start_bot
                    show_info
                else
                    log_warning "Установка завершена, но требуется редактирование .env"
                    log_info "Отредактируй: nano $INSTALL_DIR/.env"
                    log_info "Затем запусти: systemctl start $SERVICE_NAME"
                fi
                ;;
            
            2)
                log_info "Обновление кода и перезагрузка..."
                update_code
                log_success "Готово!"
                ;;
            
            3)
                log_info "Обновление зависимостей Python..."
                cd "$INSTALL_DIR"
                source venv/bin/activate
                pip install -r requirements.txt -q
                log_success "Зависимости обновлены"
                ;;
            
            4)
                show_status
                ;;
            
            5)
                show_logs
                ;;
            
            6)
                log_info "До встречи!"
                exit 0
                ;;
            
            *)
                log_error "Неверный выбор"
                ;;
        esac
    done
}

# Запуск
main

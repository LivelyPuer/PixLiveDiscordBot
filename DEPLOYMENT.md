# 🚀 Развертывание PixLive Discord Bot

Полное руководство по развертыванию бота на сервер с автозапуском и автообновлением.

## 📦 Быстрое развертывание (одна команда)

### На новый сервер (с интернетом)

```bash
# Загрузить и запустить скрипт установки
curl -fsSL https://raw.githubusercontent.com/LivelyPuer/PixLiveDiscordBot/main/install.sh | sudo bash
```

### Локально или с репозитория

```bash
sudo bash install.sh
```

Скрипт автоматически:
- ✅ Определит ОС (Ubuntu/Debian, CentOS/RHEL, Alpine)
- ✅ Установит системные зависимости (Python 3, git, build-tools)
- ✅ Создаст пользователя `pixlive`
- ✅ Клонирует репозиторий в `/opt/PixLiveDiscordBot`
- ✅ Создаст виртуальное окружение Python
- ✅ Установит зависимости из `requirements.txt`
- ✅ Создаст systemd сервис
- ✅ Включит автозапуск при старте системы
- ✅ Запустит сервис

## ⚙️ Конфигурация

После установки нужно отредактировать файл конфигурации:

```bash
nano /opt/PixLiveDiscordBot/.env
```

### Требуемые переменные окружения

```env
# Discord Bot
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=123456789  # Channel ID where to post

# Telegram Admin Bot
TG_BOT_TOKEN=your_telegram_bot_token_here
TG_ADMIN_PASSWORD=your_secure_password_here

# DeviantArt API
DEVIANTART_CLIENT_ID=your_client_id
DEVIANTART_CLIENT_SECRET=your_client_secret
DEVIANTART_USERNAMES=artist1,artist2,artist3

# Optional settings
POLL_INTERVAL_SECONDS=60
STATE_FILE=data/state.json
```

Где получить токены подробно описано в [SETUP.md](SETUP.md).

## 🎮 Управление сервисом

После установки сервис `pixlive` работает под управлением systemd.

### Основные команды

```bash
# Проверить статус
sudo systemctl status pixlive

# Запустить сервис
sudo systemctl start pixlive

# Остановить сервис
sudo systemctl stop pixlive

# Перезагрузить сервис
sudo systemctl restart pixlive

# Проверить автозапуск
sudo systemctl is-enabled pixlive
```

## 📋 Логи

Все логи сохраняются в systemd journal:

```bash
# Живые логи (нажми Ctrl+C для выхода)
sudo journalctl -u pixlive -f

# Последние 100 строк
sudo journalctl -u pixlive -n 100

# Логи за последний час
sudo journalctl -u pixlive --since "1 hour ago"

# Ошибки
sudo journalctl -u pixlive -p err
```

## 🔄 Обновление кода

### Способ 1: Используя скрипт обновления

```bash
cd /opt/PixLiveDiscordBot
sudo bash update.sh
```

### Способ 2: Вручную

```bash
cd /opt/PixLiveDiscordBot
sudo git pull origin main
sudo /opt/PixLiveDiscordBot/venv/bin/pip install -r requirements.txt
sudo systemctl restart pixlive
```

## 🛠️ Дополнительные скрипты

В проекте есть несколько полезных скриптов:

### `deploy.sh` - Полное управление (требует root)

Интерактивное меню для полного управления:

```bash
sudo bash /opt/PixLiveDiscordBot/deploy.sh
```

Или команды напрямую:

```bash
# Полная установка
sudo bash /opt/PixLiveDiscordBot/deploy.sh install

# Обновление
sudo bash /opt/PixLiveDiscordBot/deploy.sh update

# Управление
sudo bash /opt/PixLiveDiscordBot/deploy.sh start
sudo bash /opt/PixLiveDiscordBot/deploy.sh stop
sudo bash /opt/PixLiveDiscordBot/deploy.sh restart

# Информация
sudo bash /opt/PixLiveDiscordBot/deploy.sh status
sudo bash /opt/PixLiveDiscordBot/deploy.sh logs
```

### `run.sh` - Локальный запуск (без root)

Для локальной разработки и тестирования:

```bash
bash /opt/PixLiveDiscordBot/run.sh
```

Скрипт автоматически:
- Создаст виртуальное окружение если нужно
- Установит зависимости
- Создаст .env из примера если требуется
- Запустит бота

### `update.sh` - Быстрое обновление

Простой скрипт для обновления кода и перезагрузки:

```bash
sudo bash /opt/PixLiveDiscordBot/update.sh
```

## 🔐 Автозапуск при старте сервера

Автозапуск включается автоматически при установке. Бот будет:
- ✅ Запускаться при старте сервера
- ✅ Автоматически перезагружаться если упадет (каждые 10 секунд попытается запуститься)
- ✅ Логироваться в systemd journal

Проверить статус автозапуска:

```bash
sudo systemctl is-enabled pixlive
```

## 📊 Структура папок на сервере

```
/opt/PixLiveDiscordBot/
├── main.py                 # Точка входа
├── requirements.txt        # Python зависимости
├── .env                    # Конфигурация (секретная)
├── .env.example           # Пример конфигурации
├── README.md              # Основная документация
├── SETUP.md               # Детальная инструкция по токенам
├── DEPLOYMENT.md          # Этот файл
├── install.sh             # Скрипт установки (одна команда)
├── deploy.sh              # Полное управление
├── update.sh              # Обновление
├── run.sh                 # Локальный запуск
├── venv/                  # Виртуальное окружение Python
├── data/
│   └── state.json        # Сохраненное состояние (ID последних постов)
├── bot/
│   ├── discord_bot.py    # Discord интеграция
│   ├── telegram_admin.py # Telegram админ-бот
│   ├── config.py         # Загрузка конфигурации
│   └── state.py          # Управление состоянием
├── services/
│   └── deviantart/
│       └── service.py    # DeviantArt интеграция
└── tests/
    ├── test_deviantart.py
    └── test_integration.py
```

## ✅ Проверка установки

После установки проверь что все работает:

```bash
# 1. Проверить статус сервиса
sudo systemctl status pixlive

# 2. Посмотреть логи (должны быть ошибок о конфигурации если .env правильный)
sudo journalctl -u pixlive -f

# 3. Убедиться что процесс запущен
ps aux | grep "python main.py"

# 4. Проверить порты если используются
sudo netstat -tlnp | grep python

# 5. Убедиться что есть доступ в интернет для git и API
curl -I https://github.com
curl -I https://www.deviantart.com/api/v1
```

## 🐛 Решение проблем

### Сервис не запускается

```bash
# Посмотри ошибки
sudo journalctl -u pixlive -n 50

# Проверь конфигурацию
cat /opt/PixLiveDiscordBot/.env
nano /opt/PixLiveDiscordBot/.env

# Попытайся запустить вручную
cd /opt/PixLiveDiscordBot
/opt/PixLiveDiscordBot/venv/bin/python main.py
```

### Ошибка при обновлении

```bash
# Проверь статус git
cd /opt/PixLiveDiscordBot
git status
git log -1

# Попытайся обновить вручную
git fetch origin
git reset --hard origin/main
/opt/PixLiveDiscordBot/venv/bin/pip install -r requirements.txt
sudo systemctl restart pixlive
```

### Пост не публикуется

1. Проверь `DISCORD_CHANNEL_ID` - он должен быть правильным
2. Убедись что бот добавлен на сервер Discord с правами на отправку сообщений
3. Проверь `DEVIANTART_USERNAMES` - выполняются ли они правильно
4. Посмотри логи для деталей ошибок

### Telegram не отвечает

1. Проверь `TG_BOT_TOKEN` - правильный ли токен от @BotFather
2. Убедись что написал боту `/auth your_password` (вместо вашего пароля из .env)
3. Проверь что сервер имеет доступ в интернет к Telegram API

## 🔄 Автоматическое обновление

Для автоматического обновления кода каждый день можно добавить cron задачу:

```bash
sudo crontab -e
```

Добавить строку:

```cron
# Обновлять код каждый день в 2:00 AM
0 2 * * * cd /opt/PixLiveDiscordBot && git pull origin main && /opt/PixLiveDiscordBot/venv/bin/pip install -r requirements.txt && systemctl restart pixlive
```

Или использовать systemd timer (рекомендуется):

```bash
sudo nano /etc/systemd/system/pixlive-update.service
```

```ini
[Unit]
Description=Update PixLive Bot
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/opt/PixLiveDiscordBot
ExecStart=/bin/bash -c 'git pull origin main && /opt/PixLiveDiscordBot/venv/bin/pip install -r requirements.txt && systemctl restart pixlive'
```

Потом:

```bash
sudo nano /etc/systemd/system/pixlive-update.timer
```

```ini
[Unit]
Description=Update PixLive Bot Daily

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Активировать:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pixlive-update.timer
sudo systemctl start pixlive-update.timer

# Проверить
sudo systemctl list-timers pixlive-update.timer
```

## 📞 Поддержка

Если возникли проблемы:

1. Проверь документацию [README.md](README.md) и [SETUP.md](SETUP.md)
2. Посмотри логи: `sudo journalctl -u pixlive -f`
3. Убедись что все токены правильно установлены в `.env`
4. Создай issue на GitHub: https://github.com/LivelyPuer/PixLiveDiscordBot/issues

---

**Счастливого деплоя! 🚀**

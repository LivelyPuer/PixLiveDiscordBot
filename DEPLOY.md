# 🚀 Развертывание PixLive Bot на сервер

## 📋 Требования

- Linux сервер (Ubuntu/Debian рекомендуется)
- Python 3.8+
- SSH доступ
- ~200 MB свободного места

---

## 🔧 Вариант 1: Простое развертывание (screen/tmux)

### 1. Подключение к серверу

```bash
ssh user@your_server_ip
```

### 2. Установка зависимостей

```bash
# Обновить пакеты
sudo apt update && sudo apt upgrade -y

# Установить Python и необходимые инструменты
sudo apt install -y python3 python3-pip python3-venv git screen

# Или если используешь tmux
sudo apt install -y tmux
```

### 3. Клонирование проекта

```bash
cd /opt  # или выбери другую директорию

git clone https://github.com/yourusername/PixLiveDiscordBot.git
cd PixLiveDiscordBot
```

### 4. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### 5. Настройка .env

```bash
nano .env
# Заполни все переменные из .env.example
# Ctrl+X → Y → Enter для сохранения
```

### 6. Запуск в screen (фоновый режим)

```bash
# Создать новый screen сеанс
screen -S pixlive

# Запустить бота
python main.py

# Отсоединиться: Ctrl+A → D

# Позже подключиться обратно:
screen -r pixlive

# Убить сеанс:
screen -X -S pixlive quit
```

**Или используй tmux:**

```bash
# Создать новый tmux сеанс
tmux new-session -d -s pixlive -c /opt/PixLiveDiscordBot

# Запустить бота в сеансе
tmux send-keys -t pixlive "source venv/bin/activate && python main.py" Enter

# Подключиться к сеансу:
tmux attach -t pixlive

# Отсоединиться: Ctrl+B → D
```

---

## 🔧 Вариант 2: Systemd сервис (рекомендуется)

### 1-5. Выполни шаги выше (клонирование, виртуальное окружение, .env)

### 6. Создание systemd сервиса

```bash
# Создай файл сервиса
sudo nano /etc/systemd/system/pixlive.service
```

**Содержимое файла:**

```ini
[Unit]
Description=PixLive Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=your_username  # ← Замени на свой username
WorkingDirectory=/opt/PixLiveDiscordBot
Environment="PATH=/opt/PixLiveDiscordBot/venv/bin"
ExecStart=/opt/PixLiveDiscordBot/venv/bin/python main.py

# Автоматический перезапуск при падении
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 7. Включение сервиса

```bash
# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозагрузку
sudo systemctl enable pixlive

# Запустить сервис
sudo systemctl start pixlive

# Проверить статус
sudo systemctl status pixlive

# Просмотреть логи
sudo journalctl -u pixlive -f
```

### 8. Полезные команды

```bash
# Перезагрузить конфиг
sudo systemctl reload pixlive

# Остановить
sudo systemctl stop pixlive

# Перезагрузить сервер
sudo reboot
# Бот автоматически запустится после перезагрузки
```

---

## 🐳 Вариант 3: Docker (продвинутый)

### 1. Установка Docker

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose

# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Создание Dockerfile

```bash
cat > /opt/PixLiveDiscordBot/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать код
COPY . .

# Запустить бота
CMD ["python", "main.py"]
EOF
```

### 3. Создание docker-compose.yml

```bash
cat > /opt/PixLiveDiscordBot/docker-compose.yml << 'EOF'
version: '3.8'

services:
  pixlive:
    build: .
    container_name: pixlive_bot
    restart: always
    env_file: .env
    volumes:
      - ./data:/app/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
```

### 4. Запуск Docker контейнера

```bash
cd /opt/PixLiveDiscordBot

# Собрать образ
docker-compose build

# Запустить контейнер
docker-compose up -d

# Проверить логи
docker-compose logs -f

# Остановить
docker-compose down

# Перезагрузить
docker-compose restart
```

---

## 📊 Сравнение способов

| Способ | Простота | Надежность | Автозагрузка | Рекомендуется |
|--------|----------|-----------|--------------|--------------|
| Screen/Tmux | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ | Для тестирования |
| Systemd | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | **Production** |
| Docker | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | Production+ |

---

## 🔍 Проверка после развертывания

### 1. Проверить статус бота

```bash
# Systemd
sudo systemctl status pixlive

# Docker
docker ps | grep pixlive

# Screen
screen -ls
```

### 2. Проверить логи

```bash
# Systemd
sudo journalctl -u pixlive -n 50

# Docker
docker logs -f pixlive_bot

# Screen
screen -r pixlive
```

### 3. Проверить что конфиг правильный

```bash
cd /opt/PixLiveDiscordBot
python check_config.py
```

### 4. Запустить тесты

```bash
python test_deviantart.py
python test_integration.py
```

---

## ⚠️ Важные замечания

### Безопасность .env файла

```bash
# Убедись что .env не лежит в git
cat .gitignore | grep .env

# Установи правильные права доступа
chmod 600 /opt/PixLiveDiscordBot/.env

# Убедись что только нужный пользователь может читать
ls -la /opt/PixLiveDiscordBot/.env
# -rw------- 1 user user
```

### Логирование

Боты логируют в консоль. Убедись что логи сохраняются:

```bash
# Systemd автоматически логирует в journalctl
sudo journalctl -u pixlive --since today

# Docker логирует в stdout
docker logs pixlive_bot

# Можно перенаправить в файл
nohup python main.py > bot.log 2>&1 &
tail -f bot.log
```

### Обновление кода

```bash
cd /opt/PixLiveDiscordBot

# Обновить из git
git pull origin main

# Переустановить зависимости (если изменились)
source venv/bin/activate
pip install -r requirements.txt

# Перезагрузить сервис
sudo systemctl restart pixlive
```

---

## 🆘 Troubleshooting

### Бот не запускается

```bash
# Проверить логи
sudo journalctl -u pixlive -n 100

# Проверить конфиг
python check_config.py

# Проверить права доступа файлов
ls -la /opt/PixLiveDiscordBot/
```

### Бот падает после запуска

```bash
# Запустить вручную и смотреть ошибки
source venv/bin/activate
python main.py

# Проверить что все токены правильные
cat .env | grep TOKEN
```

### Высокий CPU или память

```bash
# Проверить процессы
ps aux | grep python

# Посмотреть использование памяти
free -h

# Если слишком много памяти - может быть утечка в коде
# Увеличить интервал опроса в .env:
POLL_INTERVAL_SECONDS=300  # 5 минут вместо 60 секунд
```

### Нет постов в Discord

```bash
# 1. Проверить что бот подключен
sudo journalctl -u pixlive | grep "ready"

# 2. Проверить что Channel ID правильный
python test_integration.py

# 3. Проверить права бота в Discord
# В Discord Settings → Roles → выбери роль бота → проверь права

# 4. Проверить логи DeviantArt API
python test_deviantart.py
```

---

## 📞 Быстрая помощь

```bash
# Быстро перезагрузить бота
sudo systemctl restart pixlive && sudo journalctl -u pixlive -f

# Посмотреть последние 50 строк логов
sudo journalctl -u pixlive -n 50 --no-pager

# Посмотреть ошибки за последний час
sudo journalctl -u pixlive --since "1 hour ago" | grep -i error

# Убить процесс вручную (если заморозился)
pkill -f "python main.py"
```

---

**Готово! Бот развернут и работает на сервере!** 🎉

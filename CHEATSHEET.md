# 🚀 ШПАРГАЛКА - PixLive Discord Bot Deployment

## ⚡ ОДНА КОМАНДА ДЛЯ ДЕПЛОЯ

```bash
curl -fsSL https://raw.githubusercontent.com/LivelyPuer/PixLiveDiscordBot/main/install.sh | sudo bash
```

Вот и всё! 🎉 Бот будет:
- ✅ Установлен в `/opt/PixLiveDiscordBot`
- ✅ Работать 24/7 с автозапуском
- ✅ Перезагружаться если упадет
- ✅ Логироваться в systemd journal

## 📋 Быстрые команды

### Управление
```bash
sudo systemctl start pixlive      # Запустить
sudo systemctl stop pixlive       # Остановить
sudo systemctl restart pixlive    # Перезагрузить
sudo systemctl status pixlive     # Статус
```

### Логи и информация
```bash
sudo journalctl -u pixlive -f     # Живые логи (Ctrl+C = выход)
sudo journalctl -u pixlive -n 50  # Последние 50 строк
```

### Обновление
```bash
sudo bash /opt/PixLiveDiscordBot/update.sh  # Одна команда
# или
cd /opt/PixLiveDiscordBot && sudo git pull && sudo systemctl restart pixlive
```

### Конфигурация
```bash
sudo nano /opt/PixLiveDiscordBot/.env       # Отредактировать токены
sudo systemctl restart pixlive              # Перезагрузить после изменений
```

## 📁 Основные файлы

| Файл | Использование | Требует sudo |
|------|---------------|-------------|
| `install.sh` | Полная установка на сервер | ✅ |
| `deploy.sh` | Интерактивное управление | ✅ |
| `update.sh` | Обновление с GitHub | ✅ |
| `run.sh` | Локальный запуск | ❌ |

## 🎯 Типичные сценарии

### Новый сервер
```bash
sudo bash install.sh
sudo nano /opt/PixLiveDiscordBot/.env    # Добавить токены
sudo systemctl status pixlive             # Проверить
```

### Обновить код
```bash
sudo bash /opt/PixLiveDiscordBot/update.sh
```

### Локальная разработка
```bash
bash run.sh
# Ctrl+C для выхода
```

### Что-то не работает?
```bash
# 1. Посмотреть логи
sudo journalctl -u pixlive -f

# 2. Проверить конфиг
cat /opt/PixLiveDiscordBot/.env

# 3. Перезагрузить
sudo systemctl restart pixlive

# 4. Если совсем плохо
sudo bash /opt/PixLiveDiscordBot/deploy.sh install
```

## 🔧 Конфигурация (.env)

```env
DISCORD_TOKEN=your_discord_token
DISCORD_CHANNEL_ID=123456789
TG_BOT_TOKEN=your_telegram_token
TG_ADMIN_PASSWORD=your_password
DEVIANTART_CLIENT_ID=your_id
DEVIANTART_CLIENT_SECRET=your_secret
DEVIANTART_USERNAMES=artist1,artist2
```

## ✨ Что автоматически делает systemd

- 🔄 Запускает при старте сервера
- 🔁 Перезагружает если упадет (каждые 10 сек)
- 📋 Логирует в journal
- 🔐 Запускает под пользователем `pixlive`

## 📚 Подробнее

- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [DEPLOYMENT.md](DEPLOYMENT.md) - Полная документация
- [SCRIPTS_FULL.md](SCRIPTS_FULL.md) - Все скрипты

---

**Главное**: используй `install.sh` один раз, потом всё работает автоматически! 🚀

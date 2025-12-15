# Инструкция по настройке PixLive Bot

## 📋 Что нужно в `.env`

```env
# Discord Bot
DISCORD_TOKEN=<your_bot_token>
DISCORD_CHANNEL_ID=<channel_id>

# Telegram Admin Bot
TG_BOT_TOKEN=<your_tg_bot_token>
TG_ADMIN_PASSWORD=<secure_password>

# DeviantArt API
DEVIANTART_CLIENT_ID=<client_id>
DEVIANTART_CLIENT_SECRET=<client_secret>
DEVIANTART_USERNAMES=artist1,artist2

# Optional
POLL_INTERVAL_SECONDS=60
STATE_FILE=data/state.json
```

## 🎯 Где получить токены и ID

### 1️⃣ Discord Bot Token и Channel ID

**Получить токен:**
- Перейди на https://discord.com/developers/applications
- Нажми "New Application"
- В левом меню: OAuth2 → Bot → "Add Bot"
- Скопируй токен в `DISCORD_TOKEN`

**Получить Channel ID:**
- Включи Developer Mode в Discord (User Settings → Advanced → Developer Mode)
- Кликни правой кнопкой по каналу → Copy Channel ID
- Вставь в `DISCORD_CHANNEL_ID`

### 2️⃣ DeviantArt API Credentials

- Перейди на https://www.deviantart.com/developers/register
- Залогинься или создай аккаунт
- Создай приложение (Application)
- Скопируй `Client ID` → `DEVIANTART_CLIENT_ID`
- Скопируй `Client Secret` → `DEVIANTART_CLIENT_SECRET`

**Список художников:**
- `DEVIANTART_USERNAMES=artistname1,artistname2`
- Можешь добавлять/удалять художников без перезагрузки

### 3️⃣ Telegram Admin Bot Token

- Напиши `@BotFather` в Telegram
- `/newbot` → создай нового бота
- Скопируй токен в `TG_BOT_TOKEN`
- Установи пароль в `TG_ADMIN_PASSWORD` (любая строка)

**Как использовать:**
- Напиши боту: `/auth your_password`
- Команды:
  - `/status` — статистика постов
  - `/pause deviantart:artistname` — остановить отслеживание
  - `/resume deviantart:artistname` — возобновить

## 🚀 Запуск

```bash
# 1. Скопируй .env.example в .env и заполни
cp .env.example .env

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Запусти бота
python main.py
```

## ✅ Проверка ошибок

**Если бот не запускается:**
- Проверь что все токены и ID правильные
- Посмотри логи в консоли
- Убедись что бот добавлен на сервер в Discord

**Если посты не публикуются:**
- Проверь что `DISCORD_CHANNEL_ID` правильный
- Убедись что бот имеет права на отправку сообщений в канал

**Если Telegram не работает:**
- Проверь `TG_BOT_TOKEN`
- Убедись что написал боту `/auth password`

## 📊 Архитектура

- **Discord Bot** — отправляет посты когда их находит
- **DeviantArt Service** — опрашивает API каждые N секунд
- **Telegram Admin** — управление и аналитика
- **State File** — хранит ID последнего поста чтобы не дублировать


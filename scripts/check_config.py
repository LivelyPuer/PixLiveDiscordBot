#!/usr/bin/env python3
"""
Проверяет что все настройки правильные перед запуском бота
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

checks = {
    "✅ Все хорошо": [],
    "⚠️ Предупреждение": [],
    "❌ Критическая ошибка": [],
}

# Discord
discord_token = os.getenv("DISCORD_TOKEN", "").strip()
discord_channel_id = os.getenv("DISCORD_CHANNEL_ID", "").strip()

if not discord_token:
    checks["❌ Критическая ошибка"].append("DISCORD_TOKEN не установлен")
else:
    checks["✅ Все хорошо"].append("DISCORD_TOKEN установлен")

if not discord_channel_id:
    checks["❌ Критическая ошибка"].append("DISCORD_CHANNEL_ID не установлен")
elif not discord_channel_id.isdigit():
    checks["❌ Критическая ошибка"].append("DISCORD_CHANNEL_ID должен быть числом")
else:
    checks["✅ Все хорошо"].append(f"DISCORD_CHANNEL_ID установлен: {discord_channel_id}")

# DeviantArt
da_client_id = os.getenv("DEVIANTART_CLIENT_ID", "").strip()
da_client_secret = os.getenv("DEVIANTART_CLIENT_SECRET", "").strip()
da_usernames = os.getenv("DEVIANTART_USERNAMES", "").strip()

if not da_client_id:
    checks["❌ Критическая ошибка"].append("DEVIANTART_CLIENT_ID не установлен")
else:
    checks["✅ Все хорошо"].append("DEVIANTART_CLIENT_ID установлен")

if not da_client_secret:
    checks["❌ Критическая ошибка"].append("DEVIANTART_CLIENT_SECRET не установлен")
else:
    checks["✅ Все хорошо"].append("DEVIANTART_CLIENT_SECRET установлен")

if not da_usernames:
    checks["❌ Критическая ошибка"].append("DEVIANTART_USERNAMES не установлен (используй формат: artist1,artist2)")
else:
    usernames = [u.strip() for u in da_usernames.split(",") if u.strip()]
    checks["✅ Все хорошо"].append(f"DEVIANTART_USERNAMES установлен ({len(usernames)} художников): {', '.join(usernames)}")

# Telegram
tg_token = os.getenv("TG_BOT_TOKEN", "").strip()
tg_password = os.getenv("TG_ADMIN_PASSWORD", "").strip()

if not tg_token:
    checks["❌ Критическая ошибка"].append("TG_BOT_TOKEN не установлен")
else:
    checks["✅ Все хорошо"].append("TG_BOT_TOKEN установлен")

if not tg_password:
    checks["⚠️ Предупреждение"].append("TG_ADMIN_PASSWORD не установлен (используется пустой пароль)")
else:
    checks["✅ Все хорошо"].append(f"TG_ADMIN_PASSWORD установлен ({len(tg_password)} символов)")

# Optional settings
poll_interval = os.getenv("POLL_INTERVAL_SECONDS", "60").strip()
state_file = os.getenv("STATE_FILE", "data/state.json").strip()

if poll_interval.isdigit() and int(poll_interval) > 0:
    checks["✅ Все хорошо"].append(f"Интервал опроса: {poll_interval}с")
else:
    checks["⚠️ Предупреждение"].append("POLL_INTERVAL_SECONDS должен быть положительным числом")

checks["✅ Все хорошо"].append(f"Файл состояния: {state_file}")

# Print results
print("\n" + "="*60)
print("📋 ПРОВЕРКА КОНФИГУРАЦИИ PixLive Bot")
print("="*60 + "\n")

for category, items in checks.items():
    if items:
        print(f"\n{category}")
        for item in items:
            print(f"  {item}")

has_critical = bool(checks["❌ Критическая ошибка"])

print("\n" + "="*60)
if has_critical:
    print("❌ ИСПРАВЬТЕ ОШИБКИ ПЕРЕД ЗАПУСКОМ")
    sys.exit(1)
else:
    print("✅ КОНФИГУРАЦИЯ ВАЛИДНА - ГОТОВО К ЗАПУСКУ")
    sys.exit(0)

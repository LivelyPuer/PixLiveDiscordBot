#!/usr/bin/env python3
"""
Интеграционный тест - проверяет DeviantArt сервис и mock Discord канал
без запуска реального Discord бота
"""
import asyncio
import sys
import os

# Добавить родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()
from bot.config import cfg
from bot.state import StateStore
from services.deviantart.service import DeviantArtService


class MockDiscordChannel:
    """Mock Discord канал для тестирования."""
    
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.messages = []
    
    async def send(self, **kwargs):
        """Mock send message."""
        msg = {
            "embed": kwargs.get("embed"),
            "content": kwargs.get("content"),
            "timestamp": asyncio.get_event_loop().time()
        }
        self.messages.append(msg)
        
        # Print message to console
        embed = msg.get("embed")
        if embed:
            print(f"\n📨 Сообщение отправлено в канал #{self.channel_id}:")
            print(f"   Заголовок: {embed.title}")
            print(f"   Описание: {embed.description}")
            print(f"   URL: {embed.url}")
            if embed.image:
                print(f"   Изображение: {embed.image.url}")
        else:
            print(f"\n💬 {msg.get('content')}")


async def test_with_mock_discord():
    """Test DeviantArt service with mock Discord channel."""
    
    print("="*70)
    print("🧪 ИНТЕГРАЦИОННЫЙ ТЕСТ - DeviantArt + Mock Discord")
    print("="*70)
    
    # Validate config
    if not cfg.deviantart_client_id or not cfg.deviantart_client_secret:
        print("❌ DeviantArt credentials не установлены в .env")
        return False
    
    usernames = [u.strip() for u in cfg.deviantart_usernames.split(",") if u.strip()]
    if not usernames:
        print("❌ DEVIANTART_USERNAMES не установлен в .env")
        return False
    
    # Create mock channel
    mock_channel = MockDiscordChannel(cfg.discord_channel_id)
    
    # Create state store
    state = StateStore(cfg.state_file)
    
    # Mock Discord Embed
    class MockEmbed:
        def __init__(self, **kwargs):
            self.title = kwargs.get("title")
            self.url = kwargs.get("url")
            self.description = kwargs.get("description")
            self.color = kwargs.get("color")
            self.image = None
        
        def set_image(self, url):
            class Image:
                pass
            img = Image()
            img.url = url
            self.image = img
    
    print(f"\n✅ Конфигурация:")
    print(f"   Channel ID: {cfg.discord_channel_id}")
    print(f"   Художники: {', '.join(usernames)}")
    print(f"   Интервал: {cfg.poll_interval_seconds}с")
    
    all_ok = True
    for username in usernames:
        print(f"\n{'='*70}")
        print(f"🎨 Тестирование: {username}")
        print(f"{'='*70}")
        
        service = DeviantArtService(
            username,
            client_id=cfg.deviantart_client_id,
            client_secret=cfg.deviantart_client_secret,
            poll_interval=cfg.poll_interval_seconds
        )
        
        try:
            # Get one poll result
            print("\n⏳ Получение постов...")
            last_ts = await state.get(f"{username}:last_timestamp")
            new_entries = await service.poll_once(last_ts)
            
            print(f"✅ Получено {len(new_entries)} новых постов")
            
            if new_entries:
                # Simulate posting to Discord
                print(f"\n📤 Отправка в Discord...")
                for i, deviation in enumerate(new_entries[:2], 1):  # Show first 2
                    title = deviation.get("title", "No title")
                    url = deviation.get("url", "#")
                    thumbs = deviation.get("thumbs", [])
                    # thumbs is a list of dicts with 'src', 'height', 'width'
                    thumb_url = None
                    if thumbs:
                        thumb_obj = thumbs[0]
                        if isinstance(thumb_obj, dict):
                            thumb_url = thumb_obj.get("src")
                        else:
                            thumb_url = str(thumb_obj)
                    
                    # Create embed
                    embed = MockEmbed(
                        title=title,
                        url=url,
                        description=f"New post from {username}",
                        color=0x0000FF
                    )
                    if thumb_url:
                        embed.set_image(url=thumb_url)
                    
                    # Send to mock channel
                    await mock_channel.send(embed=embed)
                    
                    # Update state
                    ts = deviation.get("published_time") or deviation.get("date")
                    if ts:
                        await state.set(f"{username}:last_timestamp", ts)
                        await state.update("analytics:posts_sent", lambda v: (v or 0) + 1)
                
                if len(new_entries) > 2:
                    print(f"\n... и еще {len(new_entries) - 2} постов (не показаны)")
            else:
                print("⚠️  Нет новых постов (галерея может быть пуста или уже обновлена)")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            all_ok = False
    
    # Show statistics
    print(f"\n{'='*70}")
    print("📊 СТАТИСТИКА")
    print(f"{'='*70}")
    
    total_sent = await state.get("analytics:posts_sent", 0)
    print(f"✅ Всего отправлено постов: {total_sent}")
    print(f"✅ Отправленных сообщений в этом тесте: {len(mock_channel.messages)}")
    
    print(f"\n{'='*70}")
    if all_ok and len(mock_channel.messages) > 0:
        print("✅ ИНТЕГРАЦИОННЫЙ ТЕСТ ПРОЙДЕН")
        print("Сервис готов к работе с Discord ботом!")
    elif all_ok:
        print("⚠️  ТЕСТ ПРОЙДЕН, НО НЕТУ НОВЫХ ПОСТОВ")
        print("Возможно, галерея уже обновлена или пуста")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
    print(f"{'='*70}\n")
    
    return all_ok


async def interactive_test():
    """Interactive test with multiple attempts."""
    
    print("\n" + "="*70)
    print("🔄 ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("="*70)
    
    usernames = [u.strip() for u in cfg.deviantart_usernames.split(",") if u.strip()]
    state = StateStore(cfg.state_file)
    
    while True:
        print("\nЧто хочешь проверить?")
        print("1 - Получить посты определенного художника")
        print("2 - Сбросить последний timestamp (будут получены все посты)")
        print("3 - Показать статистику")
        print("4 - Выход")
        
        choice = input("\nВыбор (1-4): ").strip()
        
        if choice == "1":
            print(f"\nДоступные художники:")
            for i, u in enumerate(usernames, 1):
                print(f"  {i} - {u}")
            
            try:
                idx = int(input("Выбор художника (номер): ")) - 1
                if 0 <= idx < len(usernames):
                    username = usernames[idx]
                    service = DeviantArtService(
                        username,
                        client_id=cfg.deviantart_client_id,
                        client_secret=cfg.deviantart_client_secret,
                    )
                    
                    last_ts = await state.get(f"{username}:last_timestamp")
                    print(f"\nПолучение постов для {username}...")
                    entries = await service.poll_once(last_ts)
                    
                    print(f"\n✅ Получено {len(entries)} постов:")
                    for i, e in enumerate(entries[:5], 1):
                        print(f"\n{i}. {e.get('title', 'No title')}")
                        print(f"   URL: {e.get('url')}")
                        print(f"   Дата: {e.get('published_time', e.get('date'))}")
            except (ValueError, IndexError):
                print("❌ Неверный выбор")
        
        elif choice == "2":
            for u in usernames:
                await state.set(f"{u}:last_timestamp", None)
            print("✅ Timestamps сброшены. При следующем опросе будут получены все посты.")
        
        elif choice == "3":
            total = await state.get("analytics:posts_sent", 0)
            print(f"\n📊 Статистика:")
            print(f"   Всего отправлено постов: {total}")
            for u in usernames:
                ts = await state.get(f"{u}:last_timestamp")
                print(f"   {u}: {ts if ts else 'Нет истории'}")
        
        elif choice == "4":
            print("👋 До встречи!")
            break
        
        else:
            print("❌ Неверный выбор")


async def main():
    """Main test runner."""
    
    if not os.path.exists(".env"):
        print("❌ Файл .env не найден! Используй: cp .env.example .env")
        return 1
    
    print("Выбери режим тестирования:")
    print("1 - Автоматический интеграционный тест")
    print("2 - Интерактивный режим")
    
    mode = input("\nВыбор (1-2): ").strip()
    
    if mode == "1":
        ok = await test_with_mock_discord()
        return 0 if ok else 1
    elif mode == "2":
        await interactive_test()
        return 0
    else:
        print("❌ Неверный выбор")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано")
        sys.exit(0)

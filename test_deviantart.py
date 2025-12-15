#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы DeviantArt сервиса
Тестирует подключение к API без запуска Discord и Telegram ботов
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load config
load_dotenv()
from bot.config import cfg
from services.deviantart.service import DeviantArtService


async def test_deviantart():
    """Test DeviantArt API connection and basic functionality."""
    
    print("="*70)
    print("🔧 ТЕСТ DeviantArt СЕРВИСА")
    print("="*70)
    
    # Validate config
    print("\n📋 Проверка конфигурации...")
    
    if not cfg.deviantart_client_id:
        print("❌ DEVIANTART_CLIENT_ID не установлен")
        return False
    print(f"✅ Client ID: {cfg.deviantart_client_id[:20]}...")
    
    if not cfg.deviantart_client_secret:
        print("❌ DEVIANTART_CLIENT_SECRET не установлен")
        return False
    print(f"✅ Client Secret: {cfg.deviantart_client_secret[:20]}...")
    
    usernames = [u.strip() for u in cfg.deviantart_usernames.split(",") if u.strip()]
    if not usernames:
        print("❌ DEVIANTART_USERNAMES не установлен")
        return False
    print(f"✅ Художники ({len(usernames)}): {', '.join(usernames)}")
    
    print(f"✅ Интервал опроса: {cfg.poll_interval_seconds}с")
    
    # Test API for each username
    all_passed = True
    for username in usernames:
        print(f"\n{'='*70}")
        print(f"🎨 Тестирование художника: {username}")
        print(f"{'='*70}")
        
        service = DeviantArtService(
            username,
            client_id=cfg.deviantart_client_id,
            client_secret=cfg.deviantart_client_secret,
            poll_interval=cfg.poll_interval_seconds
        )
        
        try:
            # Test token acquisition
            print("\n1️⃣  Получение access token...")
            import aiohttp
            async with aiohttp.ClientSession() as session:
                token = await service._get_access_token(session)
                print(f"   ✅ Token получен: {token[:30]}...")
                
                # Test gallery fetch
                print("\n2️⃣  Получение галереи...")
                data = await service.fetch_gallery(session, token)
                
                results = data.get("results", [])
                print(f"   ✅ Получено {len(results)} постов")
                
                if results:
                    print(f"\n3️⃣  Информация о последних постах:")
                    for i, deviation in enumerate(results[:3], 1):
                        title = deviation.get("title", "No title")
                        url = deviation.get("url", "#")
                        date = deviation.get("published_time", "N/A")
                        thumbs = deviation.get("thumbs", [])
                        
                        print(f"\n   Post {i}:")
                        print(f"   └─ Название: {title}")
                        print(f"   └─ URL: {url}")
                        print(f"   └─ Дата: {date}")
                        print(f"   └─ Миниатюры: {len(thumbs)} шт")
                        if thumbs:
                            # thumbs[0] is a dict with 'src', 'height', 'width'
                            thumb_obj = thumbs[0]
                            if isinstance(thumb_obj, dict):
                                thumb_url = thumb_obj.get("src", "N/A")
                            else:
                                thumb_url = str(thumb_obj)
                            print(f"      └─ Первая: {thumb_url[:60]}...")
                else:
                    print("   ⚠️  Галерея пуста или художник не существует")
                    all_passed = False
                    
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Summary
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
        print("Сервис DeviantArt работает корректно!")
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("Проверьте логи выше")
    print(f"{'='*70}\n")
    
    return all_passed


async def test_poll_cycle():
    """Test a single poll cycle to see new deviations."""
    
    print("\n" + "="*70)
    print("🔄 ТЕСТ ЦИКЛА ОПРОСА")
    print("="*70)
    
    usernames = [u.strip() for u in cfg.deviantart_usernames.split(",") if u.strip()]
    if not usernames:
        print("❌ Нет художников для тестирования")
        return
    
    username = usernames[0]
    print(f"\nТестирование цикла опроса для: {username}")
    
    service = DeviantArtService(
        username,
        client_id=cfg.deviantart_client_id,
        client_secret=cfg.deviantart_client_secret,
        poll_interval=5  # 5 секунд для быстрого теста
    )
    
    # Mock state storage
    class MockState:
        def __init__(self):
            self.data = {}
        
        async def get(self, key, default=None):
            return self.data.get(key, default)
        
        async def set(self, key, value):
            self.data[key] = value
    
    state = MockState()
    
    # Mock callback
    posts_received = []
    async def on_new_post(service_obj, deviation):
        title = deviation.get("title", "Unknown")
        posts_received.append({
            "service": service_obj.username,
            "title": title,
            "url": deviation.get("url", "#")
        })
        print(f"\n🎨 Новый пост получен:")
        print(f"   Название: {title}")
        print(f"   URL: {deviation.get('url', '#')}")
    
    try:
        print("\n⏳ Запуск одного цикла опроса (это займет несколько секунд)...")
        
        # Run one poll cycle
        async with asyncio.timeout(15):  # 15 second timeout
            await asyncio.wait_for(
                service.start(
                    state.get,
                    state.set,
                    on_new_post
                ),
                timeout=10
            )
    except asyncio.TimeoutError:
        print("\n✅ Цикл опроса завершен (timeout - это ожидаемо)")
    except Exception as e:
        print(f"\n❌ Ошибка при опросе: {e}")
        import traceback
        traceback.print_exc()
    finally:
        service.stop()
    
    print(f"\n📊 Результаты:")
    print(f"   Получено постов: {len(posts_received)}")
    if posts_received:
        print(f"   Последний пост в state: {await state.get(f'{username}:last_timestamp')}")
    
    return len(posts_received) > 0


async def main():
    """Run all tests."""
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("❌ Файл .env не найден!")
        print("   Используй: cp .env.example .env")
        print("   И заполни необходимые значения")
        return 1
    
    # Test 1: Basic API test
    api_ok = await test_deviantart()
    
    if not api_ok:
        print("\n⚠️  API тест не пройден. Проверьте конфигурацию.")
        return 1
    
    # Test 2: Poll cycle
    print("\n\nХотите протестировать полный цикл опроса? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == "y":
        poll_ok = await test_poll_cycle()
        return 0 if poll_ok else 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
Тестовый скрипт для проверки RemnaWave API
Запускайте для проверки работоспособности API перед использованием в боте
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Добавляем путь к модулям бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.bot.services.remnawave_api import RemnavaveApiClient, RemnavaveUser
from app.bot.services.remnawave_vpn import RemnavaveVPNService
from app.bot.services.remnawave_enhanced import RemnavaveEnhancedService
from app.bot.services.remnawave_server_pool import RemnavaveServerPoolService


class MockConfig:
    """Mock конфигурация для тестирования"""
    def __init__(self):
        self.remnavave = MockRemnavaveConfig()


class MockRemnavaveConfig:
    """Mock конфигурация RemnaWave"""
    def __init__(self):
        self.USERNAME = os.getenv("REMNAWAVE_USERNAME")
        self.PASSWORD = os.getenv("REMNAWAVE_PASSWORD")
        self.API_URL = os.getenv("REMNAWAVE_API_URL")
        self.SUBSCRIPTION_URL_PATH = os.getenv("REMNAWAVE_SUBSCRIPTION_PATH", "/sub")


class MockUser:
    """Mock пользователь для тестирования"""
    def __init__(self, tg_id: int):
        self.tg_id = tg_id


async def test_api_connection():
    """Тест подключения к API"""
    print("🔌 Тестирование подключения к RemnaWave API...")
    
    config = MockConfig()
    
    if not all([config.remnavave.USERNAME, config.remnavave.PASSWORD, config.remnavave.API_URL]):
        print("❌ Не заданы переменные окружения для RemnaWave API")
        print("Установите: REMNAWAVE_USERNAME, REMNAWAVE_PASSWORD, REMNAWAVE_API_URL")
        return False
    
    try:
        async with RemnavaveApiClient(
            base_url=config.remnavave.API_URL,
            username=config.remnavave.USERNAME,
            password=config.remnavave.PASSWORD
        ) as api:
            print("✅ Успешное подключение к RemnaWave API")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False


async def test_api_operations():
    """Тест основных операций API"""
    print("\n🔧 Тестирование основных операций API...")
    
    config = MockConfig()
    
    try:
        async with RemnavaveApiClient(
            base_url=config.remnavave.API_URL,
            username=config.remnavave.USERNAME,
            password=config.remnavave.PASSWORD
        ) as api:
            
            # Тест получения узлов
            print("📡 Получение узлов...")
            nodes = await api.get_all_nodes()
            if nodes is not None:
                print(f"✅ Получено {len(nodes)} узлов")
                for node in nodes[:3]:  # Показываем первые 3
                    print(f"   - {node.name} ({node.address}) - {'🟢' if node.is_node_online else '🔴'}")
            else:
                print("❌ Не удалось получить узлы")
            
            # Тест получения пользователей
            print("\n👥 Получение пользователей...")
            users = await api.get_all_users(size=5)  # Первые 5 пользователей
            if users is not None:
                print(f"✅ Получено {len(users)} пользователей")
                for user in users[:3]:  # Показываем первые 3
                    print(f"   - {user.username} - {user.status} - {user.expire_at.strftime('%Y-%m-%d')}")
            else:
                print("❌ Не удалось получить пользователей")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании операций API: {e}")
        return False


async def test_vpn_service():
    """Тест VPN сервиса"""
    print("\n🛡️ Тестирование VPN сервиса...")
    
    config = MockConfig()
    mock_user = MockUser(123456789)  # Тестовый Telegram ID
    
    try:
        vpn_service = RemnavaveVPNService(config, None, None)
        
        # Тест проверки существования клиента
        print("🔍 Проверка существования клиента...")
        client_exists = await vpn_service.is_client_exists(mock_user)
        if client_exists:
            print(f"✅ Клиент найден: {client_exists.username}")
            
            # Тест получения данных клиента
            print("📊 Получение данных клиента...")
            client_data = await vpn_service.get_client_data(mock_user)
            if client_data:
                print(f"✅ Данные получены: {client_data.max_devices} устройств, {client_data.traffic_total // 1024**3} GB")
            else:
                print("❌ Не удалось получить данные клиента")
        else:
            print("ℹ️ Клиент не найден (это нормально для нового пользователя)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании VPN сервиса: {e}")
        return False


async def test_enhanced_service():
    """Тест расширенного сервиса"""
    print("\n🚀 Тестирование расширенного сервиса...")
    
    config = MockConfig()
    mock_user = MockUser(123456789)
    
    try:
        enhanced_service = RemnavaveEnhancedService(config)
        
        # Тест получения системной статистики
        print("📈 Получение системной статистики...")
        system_stats = await enhanced_service.get_system_statistics()
        if system_stats:
            print(f"✅ Статистика получена:")
            print(f"   - Пользователей: {system_stats['users']['total']}")
            print(f"   - Узлов: {system_stats['nodes']['total']}")
            print(f"   - Онлайн узлов: {system_stats['nodes']['online']}")
        else:
            print("❌ Не удалось получить системную статистику")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании расширенного сервиса: {e}")
        return False


async def test_server_pool():
    """Тест пула серверов"""
    print("\n🖥️ Тестирование пула серверов...")
    
    config = MockConfig()
    
    try:
        server_pool = RemnavaveServerPoolService(config)
        
        # Тест синхронизации узлов
        print("🔄 Синхронизация узлов...")
        sync_success = await server_pool.sync_nodes()
        if sync_success:
            print("✅ Узлы синхронизированы")
            
            # Тест получения статистики пула
            print("📊 Получение статистики пула...")
            pool_stats = await server_pool.get_pool_statistics()
            if pool_stats:
                print(f"✅ Статистика пула получена:")
                print(f"   - Всего узлов: {pool_stats['total_nodes']}")
                print(f"   - Онлайн: {pool_stats['online_nodes']}")
                print(f"   - Подключено: {pool_stats['connected_nodes']}")
                print(f"   - Работает Xray: {pool_stats['running_nodes']}")
            else:
                print("❌ Не удалось получить статистику пула")
        else:
            print("❌ Не удалось синхронизировать узлы")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании пула серверов: {e}")
        return False


async def test_subscription_operations():
    """Тест операций с подписками"""
    print("\n🔗 Тестирование операций с подписками...")
    
    config = MockConfig()
    
    try:
        async with RemnavaveApiClient(
            base_url=config.remnavave.API_URL,
            username=config.remnavave.USERNAME,
            password=config.remnavave.PASSWORD
        ) as api:
            
            # Получаем первого пользователя для тестирования
            users = await api.get_all_users(size=1)
            if not users:
                print("ℹ️ Нет пользователей для тестирования подписок")
                return True
            
            test_user = users[0]
            print(f"🧪 Тестируем с пользователем: {test_user.username}")
            
            # Тест получения информации о подписке
            print("📋 Получение информации о подписке...")
            sub_info = await api.get_subscription_info(test_user.short_uuid)
            if sub_info:
                print(f"✅ Информация о подписке получена:")
                print(f"   - Статус: {sub_info.status}")
                print(f"   - Истекает: {sub_info.expire_at.strftime('%Y-%m-%d')}")
                print(f"   - Трафик: {sub_info.used_traffic_bytes // 1024**3} GB / {sub_info.traffic_limit_bytes // 1024**3} GB")
            else:
                print("❌ Не удалось получить информацию о подписке")
            
            # Тест получения URL подписки
            print("🔗 Получение URL подписки...")
            for client_type in ["singbox", "v2ray", "clash"]:
                sub_url = await api.get_subscription_url(test_user.short_uuid, client_type)
                if sub_url:
                    print(f"✅ URL для {client_type}: получен")
                else:
                    print(f"❌ URL для {client_type}: не получен")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании подписок: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование RemnaWave API интеграции")
    print("=" * 50)
    
    tests = [
        ("Подключение к API", test_api_connection),
        ("Основные операции API", test_api_operations),
        ("VPN сервис", test_vpn_service),
        ("Расширенный сервис", test_enhanced_service),
        ("Пул серверов", test_server_pool),
        ("Операции с подписками", test_subscription_operations),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Вывод результатов
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно! RemnaWave API работает корректно.")
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте настройки и логи.")
    
    return passed == total


if __name__ == "__main__":
    # Запуск тестирования
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        sys.exit(1)
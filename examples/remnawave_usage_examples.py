#!/usr/bin/env python3
"""
Примеры использования RemnaWave API в Telegram боте
Этот файл содержит практические примеры для различных сценариев
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Добавляем путь к модулям бота
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.bot.services.remnawave_api import RemnavaveApiClient, RemnavaveUser
from app.bot.services.remnawave_vpn import RemnavaveVPNService
from app.bot.services.remnawave_enhanced import RemnavaveEnhancedService
from app.bot.services.remnawave_server_pool import RemnavaveServerPoolService


class MockConfig:
    """Mock конфигурация для примеров"""
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
    """Mock пользователь для примеров"""
    def __init__(self, tg_id: int, username: str = None):
        self.tg_id = tg_id
        self.username = username or f"user_{tg_id}"


async def example_basic_api_usage():
    """Пример базового использования RemnaWave API"""
    print("🔧 Пример 1: Базовое использование RemnaWave API")
    print("-" * 50)
    
    config = MockConfig()
    
    if not all([config.remnavave.USERNAME, config.remnavave.PASSWORD, config.remnavave.API_URL]):
        print("❌ Не заданы переменные окружения для RemnaWave API")
        return
    
    try:
        async with RemnavaveApiClient(
            base_url=config.remnavave.API_URL,
            username=config.remnavave.USERNAME,
            password=config.remnavave.PASSWORD
        ) as api:
            
            # Получение всех узлов
            print("📡 Получение узлов...")
            nodes = await api.get_all_nodes()
            if nodes:
                print(f"✅ Найдено {len(nodes)} узлов:")
                for node in nodes[:3]:  # Показываем первые 3
                    status = "🟢" if node.is_node_online else "🔴"
                    print(f"   {status} {node.name} ({node.address}) - {node.country_code}")
            
            # Получение пользователей
            print("\n👥 Получение пользователей...")
            users = await api.get_all_users(size=5)
            if users:
                print(f"✅ Найдено {len(users)} пользователей:")
                for user in users[:3]:
                    print(f"   👤 {user.username} - {user.status} - {user.expire_at.strftime('%Y-%m-%d')}")
            
            print("\n✅ Базовое использование API завершено успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def example_user_management():
    """Пример управления пользователями"""
    print("\n👤 Пример 2: Управление пользователями")
    print("-" * 50)
    
    config = MockConfig()
    mock_user = MockUser(123456789, "test_user")
    
    try:
        vpn_service = RemnavaveVPNService(config, None, None)
        
        # Проверка существования пользователя
        print("🔍 Проверка существования пользователя...")
        existing_client = await vpn_service.is_client_exists(mock_user)
        
        if existing_client:
            print(f"✅ Пользователь найден: {existing_client.username}")
            print(f"   📅 Истекает: {existing_client.expire_at.strftime('%Y-%m-%d')}")
            print(f"   📊 Трафик: {existing_client.used_traffic_bytes // 1024**3} GB / {existing_client.traffic_limit_bytes // 1024**3} GB")
            print(f"   📱 Устройств: {existing_client.hwid_device_limit}")
            
            # Получение данных клиента
            print("\n📊 Получение данных клиента...")
            client_data = await vpn_service.get_client_data(mock_user)
            if client_data:
                print(f"   📈 Макс. устройств: {client_data.max_devices}")
                print(f"   📊 Трафик остался: {client_data.traffic_remaining // 1024**3} GB")
                print(f"   ⏰ Истекает: {datetime.fromtimestamp(client_data.expiry_time).strftime('%Y-%m-%d')}")
        else:
            print("ℹ️ Пользователь не найден")
            
            # Пример создания пользователя (закомментировано для безопасности)
            # print("\n🆕 Создание нового пользователя...")
            # success = await vpn_service.create_client(
            #     user=mock_user,
            #     devices=3,
            #     duration=30,
            #     traffic_limit_gb=10,
            #     traffic_reset_strategy="MONTH"
            # )
            # if success:
            #     print("✅ Пользователь создан успешно!")
            # else:
            #     print("❌ Ошибка создания пользователя")
        
        print("\n✅ Управление пользователями завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def example_enhanced_features():
    """Пример использования расширенных возможностей"""
    print("\n🚀 Пример 3: Расширенные возможности")
    print("-" * 50)
    
    config = MockConfig()
    mock_user = MockUser(123456789)
    
    try:
        enhanced_service = RemnavaveEnhancedService(config)
        
        # Системная статистика
        print("📈 Получение системной статистики...")
        system_stats = await enhanced_service.get_system_statistics()
        if system_stats:
            print(f"   👥 Пользователей: {system_stats['users']['total']}")
            print(f"   🟢 Активных: {system_stats['users']['active']}")
            print(f"   🔴 Отключенных: {system_stats['users']['disabled']}")
            print(f"   ⏰ Истекших: {system_stats['users']['expired']}")
            print(f"   🖥️ Узлов: {system_stats['nodes']['total']}")
            print(f"   🟢 Онлайн узлов: {system_stats['nodes']['online']}")
            print(f"   📊 Трафик использовано: {system_stats['traffic']['total_used_bytes'] // 1024**3} GB")
        
        # Статистика пользователя
        print("\n👤 Статистика пользователя...")
        user_stats = await enhanced_service.get_user_statistics(mock_user)
        if user_stats:
            print(f"   🆔 UUID: {user_stats['uuid']}")
            print(f"   📱 Устройств: {user_stats['hwid_device_limit']}")
            print(f"   🏷️ Тег: {user_stats['tag'] or 'Нет'}")
            print(f"   📝 Описание: {user_stats['description'] or 'Нет'}")
        
        print("\n✅ Расширенные возможности проверены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def example_server_pool_management():
    """Пример управления пулом серверов"""
    print("\n🖥️ Пример 4: Управление пулом серверов")
    print("-" * 50)
    
    config = MockConfig()
    
    try:
        server_pool = RemnavaveServerPoolService(config)
        
        # Синхронизация узлов
        print("🔄 Синхронизация узлов...")
        sync_success = await server_pool.sync_nodes()
        if sync_success:
            print("✅ Узлы синхронизированы")
            
            # Статистика пула
            print("\n📊 Статистика пула...")
            pool_stats = await server_pool.get_pool_statistics()
            if pool_stats:
                print(f"   📈 Всего узлов: {pool_stats['total_nodes']}")
                print(f"   🟢 Онлайн: {pool_stats['online_nodes']} ({pool_stats['availability']['online_percentage']:.1f}%)")
                print(f"   🔗 Подключено: {pool_stats['connected_nodes']} ({pool_stats['availability']['connected_percentage']:.1f}%)")
                print(f"   ⚡ Работает Xray: {pool_stats['running_nodes']} ({pool_stats['availability']['running_percentage']:.1f}%)")
                
                # Статистика по странам
                if pool_stats['by_country']:
                    print("\n   🌍 По странам:")
                    for country, stats in list(pool_stats['by_country'].items())[:3]:
                        print(f"      {country}: {stats['total']} узлов ({stats['online']} онлайн)")
            
            # Получение лучшего узла
            print("\n🎯 Поиск лучшего узла...")
            best_node = await server_pool.get_best_node(criteria="latency")
            if best_node:
                print(f"   🏆 Лучший узел: {best_node.name} ({best_node.address})")
                print(f"   🌍 Страна: {best_node.country_code}")
                print(f"   📊 Статус: {'🟢 Онлайн' if best_node.is_node_online else '🔴 Офлайн'}")
            
            # Проверка здоровья узла
            if best_node:
                print(f"\n🏥 Проверка здоровья узла {best_node.name}...")
                health = await server_pool.check_node_health(best_node.uuid)
                if health:
                    print(f"   📊 Статус: {health['health_status']}")
                    if health['issues']:
                        print(f"   ⚠️ Проблемы: {', '.join(health['issues'])}")
                    else:
                        print("   ✅ Проблем не обнаружено")
        
        print("\n✅ Управление пулом серверов завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def example_subscription_operations():
    """Пример операций с подписками"""
    print("\n🔗 Пример 5: Операции с подписками")
    print("-" * 50)
    
    config = MockConfig()
    
    try:
        async with RemnavaveApiClient(
            base_url=config.remnavave.API_URL,
            username=config.remnavave.USERNAME,
            password=config.remnavave.PASSWORD
        ) as api:
            
            # Получение пользователей для тестирования
            users = await api.get_all_users(size=3)
            if not users:
                print("ℹ️ Нет пользователей для тестирования подписок")
                return
            
            test_user = users[0]
            print(f"🧪 Тестируем с пользователем: {test_user.username}")
            
            # Информация о подписке
            print("\n📋 Информация о подписке...")
            sub_info = await api.get_subscription_info(test_user.short_uuid)
            if sub_info:
                print(f"   🆔 Short UUID: {sub_info.short_uuid}")
                print(f"   📅 Истекает: {sub_info.expire_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"   📊 Трафик: {sub_info.used_traffic_bytes // 1024**3} GB / {sub_info.traffic_limit_bytes // 1024**3} GB")
                print(f"   📈 Статус: {sub_info.status}")
                print(f"   👤 Пользователь: {sub_info.username}")
            
            # URL подписок для разных клиентов
            print("\n🔗 URL подписок для разных клиентов...")
            client_types = ["singbox", "v2ray", "clash", "raw"]
            
            for client_type in client_types:
                sub_url = await api.get_subscription_url(test_user.short_uuid, client_type)
                if sub_url:
                    # Показываем только начало URL для безопасности
                    display_url = sub_url[:50] + "..." if len(sub_url) > 50 else sub_url
                    print(f"   ✅ {client_type.upper()}: {display_url}")
                else:
                    print(f"   ❌ {client_type.upper()}: не получен")
            
            # Сырые данные подписки
            print("\n📄 Сырые данные подписки...")
            raw_sub = await api.get_raw_subscription(test_user.short_uuid, with_disabled_hosts=False)
            if raw_sub:
                print(f"   ✅ Сырые данные получены")
                if 'response' in raw_sub:
                    response = raw_sub['response']
                    print(f"   📊 Количество серверов: {len(response.get('servers', []))}")
                    print(f"   📱 Количество устройств: {response.get('deviceCount', 'N/A')}")
            else:
                print("   ❌ Сырые данные не получены")
        
        print("\n✅ Операции с подписками завершены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def example_bulk_operations():
    """Пример массовых операций"""
    print("\n⚡ Пример 6: Массовые операции")
    print("-" * 50)
    
    config = MockConfig()
    
    try:
        enhanced_service = RemnavaveEnhancedService(config)
        
        # Получение пользователей по тегу
        print("🏷️ Поиск пользователей по тегу...")
        test_tag = "TEST"  # Измените на реальный тег
        users_by_tag = await enhanced_service.get_users_by_tag(test_tag)
        
        if users_by_tag:
            print(f"   ✅ Найдено {len(users_by_tag)} пользователей с тегом '{test_tag}'")
            for user in users_by_tag[:3]:
                print(f"      👤 {user.username} - {user.status}")
            
            # Пример массового обновления (закомментировано для безопасности)
            # print(f"\n🔄 Массовое обновление пользователей с тегом '{test_tag}'...")
            # updates = {
            #     "hwidDeviceLimit": 5,
            #     "description": "Обновлено через массовую операцию"
            # }
            # success = await enhanced_service.bulk_update_users_by_tag(test_tag, updates)
            # if success:
            #     print("   ✅ Массовое обновление завершено успешно!")
            # else:
            #     print("   ❌ Ошибка массового обновления")
        else:
            print(f"   ℹ️ Пользователи с тегом '{test_tag}' не найдены")
        
        # Получение всех пользователей с пагинацией
        print("\n📄 Получение всех пользователей с пагинацией...")
        all_users = await enhanced_service.get_all_users(size=10, start=0)
        if all_users:
            print(f"   ✅ Получено {len(all_users)} пользователей")
            
            # Группировка по статусу
            status_groups = {}
            for user in all_users:
                status = user.status
                if status not in status_groups:
                    status_groups[status] = 0
                status_groups[status] += 1
            
            print("   📊 Группировка по статусу:")
            for status, count in status_groups.items():
                print(f"      {status}: {count}")
        
        print("\n✅ Массовые операции завершены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def example_error_handling():
    """Пример обработки ошибок"""
    print("\n🛡️ Пример 7: Обработка ошибок")
    print("-" * 50)
    
    config = MockConfig()
    
    try:
        # Попытка подключения с неверными данными
        print("🔒 Тест подключения с неверными данными...")
        try:
            async with RemnavaveApiClient(
                base_url="https://invalid-url.com",
                username="invalid_user",
                password="invalid_password"
            ) as api:
                await api.get_all_users()
        except Exception as e:
            print(f"   ✅ Ошибка корректно обработана: {type(e).__name__}")
        
        # Тест с неверным URL
        print("\n🌐 Тест с неверным URL...")
        try:
            async with RemnavaveApiClient(
                base_url="https://invalid-remnawave-panel.com",
                username=config.remnavave.USERNAME or "test",
                password=config.remnavave.PASSWORD or "test"
            ) as api:
                await api.get_all_users()
        except Exception as e:
            print(f"   ✅ Ошибка подключения обработана: {type(e).__name__}")
        
        # Тест с корректными данными (если доступны)
        if all([config.remnavave.USERNAME, config.remnavave.PASSWORD, config.remnavave.API_URL]):
            print("\n✅ Тест с корректными данными...")
            try:
                async with RemnavaveApiClient(
                    base_url=config.remnavave.API_URL,
                    username=config.remnavave.USERNAME,
                    password=config.remnavave.PASSWORD
                ) as api:
                    # Тест получения несуществующего пользователя
                    non_existent_user = await api.get_user_by_username("non_existent_user_12345")
                    if non_existent_user is None:
                        print("   ✅ Обработка несуществующего пользователя корректна")
                    else:
                        print("   ⚠️ Неожиданный результат для несуществующего пользователя")
                        
            except Exception as e:
                print(f"   ❌ Неожиданная ошибка: {e}")
        
        print("\n✅ Обработка ошибок протестирована!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте обработки ошибок: {e}")


async def main():
    """Основная функция с примерами"""
    print("🚀 Примеры использования RemnaWave API")
    print("=" * 60)
    
    examples = [
        ("Базовое использование API", example_basic_api_usage),
        ("Управление пользователями", example_user_management),
        ("Расширенные возможности", example_enhanced_features),
        ("Управление пулом серверов", example_server_pool_management),
        ("Операции с подписками", example_subscription_operations),
        ("Массовые операции", example_bulk_operations),
        ("Обработка ошибок", example_error_handling),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            print(f"\n{'='*20} ПРИМЕР {i} {'='*20}")
            await func()
        except Exception as e:
            print(f"❌ Критическая ошибка в примере '{name}': {e}")
        
        # Пауза между примерами
        if i < len(examples):
            print("\n⏳ Пауза 2 секунды...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 Все примеры завершены!")
    print("📚 Дополнительную информацию см. в документации:")
    print("   - REMNARAVE_API_USAGE.md")
    print("   - REMNARAVE_SETUP.md")
    print("   - README_REMNARAVE.md")


if __name__ == "__main__":
    # Проверка переменных окружения
    required_vars = ["REMNAWAVE_USERNAME", "REMNAWAVE_PASSWORD", "REMNAWAVE_API_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️ ВНИМАНИЕ: Не заданы следующие переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nНекоторые примеры могут работать некорректно.")
        print("Установите переменные окружения для полного тестирования.")
        print("\nПример:")
        print("export REMNAWAVE_USERNAME='your_username'")
        print("export REMNAWAVE_PASSWORD='your_password'")
        print("export REMNAWAVE_API_URL='https://your-panel.com'")
        print()
    
    # Запуск примеров
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Примеры прерваны пользователем")
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        sys.exit(1)
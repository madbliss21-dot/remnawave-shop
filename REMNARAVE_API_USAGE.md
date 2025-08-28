# RemnaWave API Integration Guide

Этот документ описывает интеграцию RemnaWave API в Telegram бот для продажи VPN подписок.

## Обзор

RemnaWave - это современная панель управления VPN серверами, которая предоставляет REST API для управления пользователями, узлами и подписками. Бот использует этот API для:

- Создания и управления пользователями
- Получения информации о подписках
- Управления узлами серверов
- Получения статистики использования

## Основные компоненты

### 1. RemnavaveApiClient (`app/bot/services/remnawave_api.py`)

Основной клиент для работы с RemnaWave API. Обеспечивает:

- Аутентификацию с автоматическим обновлением токена
- CRUD операции с пользователями
- Управление узлами
- Получение информации о подписках

#### Ключевые методы:

```python
# Аутентификация
async with RemnavaveApiClient(base_url, username, password) as api:
    # API автоматически аутентифицируется при входе в контекст
    
# Создание пользователя
user = await api.create_user(
    username="user123",
    expire_at=datetime.now() + timedelta(days=30),
    traffic_limit_bytes=10 * 1024**3,  # 10 GB
    telegram_id=123456789,
    hwid_device_limit=3
)

# Получение пользователя
user = await api.get_user_by_telegram_id(123456789)
user = await api.get_user_by_username("user123")
user = await api.get_user_by_uuid("uuid-here")

# Обновление пользователя
updated_user = await api.update_user(
    uuid="user-uuid",
    expire_at=new_expire_date,
    traffic_limit_bytes=new_traffic_limit
)

# Управление статусом
await api.enable_user("user-uuid")
await api.disable_user("user-uuid")
await api.reset_user_traffic("user-uuid")
await api.revoke_user_subscription("user-uuid")
```

### 2. RemnavaveVPNService (`app/bot/services/remnawave_vpn.py`)

Сервис высокого уровня для работы с VPN пользователями. Предоставляет:

- Создание и управление клиентами
- Получение данных о клиентах
- Управление подписками

#### Примеры использования:

```python
# Создание нового клиента
success = await vpn_service.create_client(
    user=user,
    devices=3,
    duration=30,
    traffic_limit_gb=10,
    traffic_reset_strategy="MONTH"
)

# Получение данных клиента
client_data = await vpn_service.get_client_data(user)

# Обновление клиента
success = await vpn_service.update_client(
    user=user,
    devices=5,
    duration=60,
    traffic_limit_gb=20
)

# Продление подписки
success = await vpn_service.extend_client(
    user=user,
    days=30,
    traffic_limit_gb=15
)

# Получение URL подписки
subscription_url = await vpn_service.get_subscription_url(user, "singbox")
```

### 3. RemnavaveEnhancedService (`app/bot/services/remnawave_enhanced.py`)

Расширенный сервис с дополнительными возможностями:

- Работа с тегами пользователей
- Статистика пользователей
- Массовые операции
- Информация о подключениях

#### Примеры использования:

```python
# Получение статистики пользователя
stats = await enhanced_service.get_user_statistics(user)

# Обновление тега пользователя
success = await enhanced_service.update_user_tag(user, "PREMIUM")

# Получение пользователей по тегу
premium_users = await enhanced_service.get_users_by_tag("PREMIUM")

# Массовое обновление пользователей
success = await enhanced_service.bulk_update_users_by_tag(
    tag="PREMIUM",
    updates={"hwidDeviceLimit": 5}
)

# Получение системной статистики
system_stats = await enhanced_service.get_system_statistics()

# Получение информации о подключении
connection_info = await enhanced_service.get_user_connection_info(user)
```

### 4. RemnavaveServerPoolService (`app/bot/services/remnawave_server_pool.py`)

Сервис для управления пулом серверов:

- Синхронизация узлов
- Мониторинг состояния
- Выбор оптимальных узлов
- Статистика пула

#### Примеры использования:

```python
# Синхронизация узлов
success = await server_pool.sync_nodes()

# Получение всех узлов
all_nodes = await server_pool.get_nodes()

# Получение только онлайн узлов
online_nodes = await server_pool.get_online_nodes()

# Получение лучшего узла
best_node = await server_pool.get_best_node(criteria="latency")

# Статистика пула
pool_stats = await server_pool.get_pool_statistics()

# Проверка здоровья узла
health = await server_pool.check_node_health("node-uuid")

# Получение узлов по стране
us_nodes = await server_pool.get_nodes_by_country("US")
```

## Конфигурация

### Переменные окружения

```bash
# RemnaWave API
REMNAWAVE_USERNAME=your_username
REMNAWAVE_PASSWORD=your_password
REMNAWAVE_API_URL=https://your-remnawave-panel.com
REMNAWAVE_SUBSCRIPTION_PATH=/sub
```

### Структура конфигурации

```python
@dataclass
class RemnavaveConfig:
    USERNAME: str
    PASSWORD: str
    API_URL: str
    SUBSCRIPTION_URL_PATH: str
```

## Обработка ошибок

Все сервисы включают комплексную обработку ошибок:

- Автоматическое обновление токена при истечении
- Повторные попытки при сбоях API
- Логирование всех операций
- Graceful fallback при ошибках

## Поддерживаемые типы клиентов

RemnaWave поддерживает различные типы клиентов:

- `singbox` - SingBox
- `v2ray` - V2Ray
- `clash` - Clash
- `raw` - Сырые данные

## Стратегии сброса трафика

- `NO_RESET` - Без сброса
- `DAY` - Ежедневный сброс
- `WEEK` - Еженедельный сброс
- `MONTH` - Ежемесячный сброс

## Статусы пользователей

- `ACTIVE` - Активный
- `DISABLED` - Отключен
- `LIMITED` - Ограничен
- `EXPIRED` - Истек

## Лучшие практики

1. **Используйте контекстные менеджеры** для API клиентов
2. **Обрабатывайте ошибки** на всех уровнях
3. **Логируйте операции** для отладки
4. **Используйте fallback** при поиске пользователей
5. **Кэшируйте данные** где это возможно
6. **Мониторьте здоровье узлов** регулярно

## Пример полного рабочего процесса

```python
async def create_vpn_subscription(user: User, plan: dict):
    """Создание VPN подписки для пользователя"""
    
    # 1. Проверяем существование пользователя
    existing_client = await vpn_service.is_client_exists(user)
    
    if existing_client:
        # 2a. Обновляем существующую подписку
        success = await vpn_service.extend_client(
            user=user,
            days=plan["duration"],
            traffic_limit_gb=plan["traffic_gb"]
        )
    else:
        # 2b. Создаем новую подписку
        success = await vpn_service.create_client(
            user=user,
            devices=plan["devices"],
            duration=plan["duration"],
            traffic_limit_gb=plan["traffic_gb"],
            traffic_reset_strategy="MONTH"
        )
    
    if success:
        # 3. Получаем URL подписки
        subscription_url = await vpn_service.get_subscription_url(user, "singbox")
        
        # 4. Отправляем пользователю
        await send_subscription_to_user(user, subscription_url)
        
        # 5. Обновляем статистику
        await update_user_statistics(user)
        
        return True
    
    return False
```

## Мониторинг и отладка

### Логирование

Все операции логируются с различными уровнями:

- `DEBUG` - Детальная информация
- `INFO` - Основные операции
- `WARNING` - Предупреждения
- `ERROR` - Ошибки

### Метрики

Сервисы предоставляют различные метрики:

- Количество пользователей
- Статус узлов
- Использование трафика
- Время отклика API

## Заключение

Интеграция RemnaWave API обеспечивает надежное и масштабируемое решение для управления VPN подписками. Все сервисы спроектированы с учетом лучших практик и включают комплексную обработку ошибок.
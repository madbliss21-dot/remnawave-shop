# Установка и настройка RemnaWave интеграции

Этот документ описывает процесс установки и настройки интеграции с RemnaWave API в Telegram боте.

## Предварительные требования

### 1. RemnaWave панель
- Установленная и настроенная панель RemnaWave v2.15+
- Доступ к API панели
- Учетные данные администратора

### 2. Системные требования
- Python 3.8+
- pip или poetry для управления зависимостями
- Доступ к интернету для установки пакетов

### 3. Переменные окружения
Убедитесь, что у вас есть доступ к настройке переменных окружения для бота.

## Пошаговая установка

### Шаг 1: Клонирование репозитория

```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### Шаг 2: Установка зависимостей

Если используете pip:
```bash
pip install -r requirements.txt
```

Если используете poetry:
```bash
poetry install
```

### Шаг 3: Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта:

```bash
# RemnaWave API Configuration
REMNAWAVE_USERNAME=your_admin_username
REMNAWAVE_PASSWORD=your_admin_password
REMNAWAVE_API_URL=https://your-remnawave-panel.com
REMNAWAVE_SUBSCRIPTION_PATH=/sub

# Bot Configuration
BOT_TOKEN=your_telegram_bot_token
BOT_ADMINS=123456789,987654321
BOT_DEV_ID=123456789
BOT_SUPPORT_ID=123456789
BOT_DOMAIN=your-domain.com
BOT_PORT=8080

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=bot_database

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_NAME=0
REDIS_USERNAME=your_redis_user
REDIS_PASSWORD=your_redis_password

# Shop Configuration
SHOP_EMAIL=support@your-domain.com
SHOP_CURRENCY=RUB
SHOP_TRIAL_ENABLED=true
SHOP_TRIAL_PERIOD=3
SHOP_REFERRER_REWARD_ENABLED=true
SHOP_REFERRER_LEVEL_ONE_PERIOD=10
SHOP_REFERRER_LEVEL_ONE_RATE=50
SHOP_REFERRER_LEVEL_TWO_PERIOD=3
SHOP_REFERRER_LEVEL_TWO_RATE=5
SHOP_BONUS_DEVICES_COUNT=1

# Payment Gateways (опционально)
PAYMENT_STARS_ENABLED=true
PAYMENT_CRYPTOMUS_ENABLED=false
PAYMENT_HELEKET_ENABLED=false
PAYMENT_YOOKASSA_ENABLED=false
PAYMENT_YOOMONEY_ENABLED=false

# Logging
LOG_LEVEL=INFO
```

### Шаг 4: Настройка планов подписок

Скопируйте пример файла планов и настройте под ваши нужды:

```bash
cp plans.example.json plans.json
```

Отредактируйте `plans.json`:

```json
{
    "durations": [30, 60, 180, 365],
    "plans": [
        {
            "devices": 1,
            "prices": {
                "RUB": {
                    "30": 100,
                    "60": 180,
                    "180": 450,
                    "365": 800
                },
                "USD": {
                    "30": 1.0,
                    "60": 1.8,
                    "180": 4.5,
                    "365": 8.0
                }
            }
        },
        {
            "devices": 3,
            "prices": {
                "RUB": {
                    "30": 150,
                    "60": 270,
                    "180": 675,
                    "365": 1200
                },
                "USD": {
                    "30": 1.5,
                    "60": 2.7,
                    "180": 6.75,
                    "365": 12.0
                }
            }
        }
    ]
}
```

### Шаг 5: Настройка базы данных

Создайте базу данных PostgreSQL:

```sql
CREATE DATABASE bot_database;
CREATE USER bot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bot_database TO bot_user;
```

### Шаг 6: Настройка Redis

Установите и настройте Redis:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis

# macOS
brew install redis
```

Настройте Redis для автозапуска:

```bash
sudo systemctl enable redis
sudo systemctl start redis
```

## Тестирование установки

### Шаг 1: Запуск тестового скрипта

Перед запуском бота рекомендуется протестировать API интеграцию:

```bash
# Установите переменные окружения
export REMNAWAVE_USERNAME="your_username"
export REMNAWAVE_PASSWORD="your_password"
export REMNAWAVE_API_URL="https://your-panel.com"

# Запустите тест
python test_remnawave_api.py
```

### Шаг 2: Проверка результатов тестов

Успешный тест должен показать:

```
🧪 Тестирование RemnaWave API интеграции
==================================================
🔌 Тестирование подключения к RemnaWave API...
✅ Успешное подключение к RemnaWave API

🔧 Тестирование основных операций API...
📡 Получение узлов...
✅ Получено 5 узлов
   - US-01 (us01.your-panel.com) - 🟢
   - EU-01 (eu01.your-panel.com) - 🟢
   - ASIA-01 (asia01.your-panel.com) - 🟢

👥 Получение пользователей...
✅ Получено 3 пользователей
   - user123 - ACTIVE - 2024-12-31
   - user456 - ACTIVE - 2024-12-31
   - user789 - ACTIVE - 2024-12-31

==================================================
📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ
==================================================
Подключение к API: ✅ ПРОЙДЕН
Основные операции API: ✅ ПРОЙДЕН
VPN сервис: ✅ ПРОЙДЕН
Расширенный сервис: ✅ ПРОЙДЕН
Пул серверов: ✅ ПРОЙДЕН
Операции с подписками: ✅ ПРОЙДЕН

Итого: 6/6 тестов пройдено
🎉 Все тесты пройдены успешно! RemnaWave API работает корректно.
```

## Запуск бота

### Шаг 1: Запуск в режиме разработки

```bash
# Из корневой директории проекта
python -m app
```

### Шаг 2: Запуск через Docker (рекомендуется для продакшена)

```bash
# Сборка образа
docker build -t remnawave-bot .

# Запуск контейнера
docker run -d \
  --name remnawave-bot \
  --env-file .env \
  -p 8080:8080 \
  remnawave-bot
```

### Шаг 3: Запуск через docker-compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
```

## Проверка работоспособности

### 1. Проверка логов бота

```bash
# Если запущен через Docker
docker logs remnawave-bot

# Если запущен локально
tail -f app/logs/bot.log
```

### 2. Проверка статуса бота

Отправьте команду `/start` боту в Telegram. Бот должен ответить приветственным сообщением.

### 3. Проверка админ-панели

Отправьте команду `/admin` (только для администраторов). Должна открыться админ-панель.

## Устранение неполадок

### Проблема: "Failed to authenticate with RemnaWave API"

**Возможные причины:**
- Неверные учетные данные
- Неправильный URL API
- Панель недоступна

**Решение:**
1. Проверьте правильность `REMNAWAVE_USERNAME` и `REMNAWAVE_PASSWORD`
2. Убедитесь, что `REMNAWAVE_API_URL` доступен
3. Проверьте, что панель RemnaWave запущена

### Проблема: "No access token received from login response"

**Возможные причины:**
- Несовместимая версия RemnaWave
- Изменения в API ответе

**Решение:**
1. Обновите RemnaWave до последней версии
2. Проверьте документацию API
3. Запустите тестовый скрипт для диагностики

### Проблема: "Failed to get nodes/users"

**Возможные причины:**
- Проблемы с правами доступа
- Ошибки в API панели

**Решение:**
1. Проверьте права пользователя в RemnaWave
2. Проверьте логи панели RemnaWave
3. Убедитесь, что API включен в настройках

### Проблема: "Database connection failed"

**Возможные причины:**
- Неверные параметры подключения к БД
- База данных не запущена

**Решение:**
1. Проверьте параметры подключения к БД
2. Убедитесь, что PostgreSQL запущен
3. Проверьте права доступа пользователя БД

## Мониторинг и обслуживание

### 1. Регулярные проверки

- Мониторинг логов бота
- Проверка состояния узлов RemnaWave
- Мониторинг использования трафика

### 2. Резервное копирование

```bash
# Резервное копирование базы данных
pg_dump bot_database > backup_$(date +%Y%m%d_%H%M%S).sql

# Резервное копирование конфигурации
cp .env backup_env_$(date +%Y%m%d_%H%M%S)
cp plans.json backup_plans_$(date +%Y%m%d_%H%M%S).json
```

### 3. Обновления

```bash
# Обновление кода
git pull origin main

# Перезапуск бота
docker-compose restart bot
```

## Безопасность

### 1. Защита учетных данных

- Никогда не коммитьте `.env` файл в Git
- Используйте сильные пароли
- Регулярно меняйте пароли

### 2. Ограничение доступа

- Настройте файрвол для ограничения доступа к API
- Используйте HTTPS для API
- Ограничьте доступ к админ-панели

### 3. Мониторинг безопасности

- Регулярно проверяйте логи на подозрительную активность
- Мониторьте количество неудачных попыток входа
- Настройте уведомления о критических событиях

## Поддержка

При возникновении проблем:

1. Проверьте логи бота и панели RemnaWave
2. Запустите тестовый скрипт для диагностики
3. Проверьте документацию RemnaWave API
4. Обратитесь к сообществу или в поддержку

## Заключение

После успешной установки и настройки у вас будет полностью функциональный Telegram бот для продажи VPN подписок, интегрированный с RemnaWave панелью. Бот поддерживает все основные функции:

- Создание и управление пользователями
- Автоматическое продление подписок
- Система промокодов
- Реферальная система
- Множественные способы оплаты
- Админ-панель для управления
- Мониторинг и статистика
# RemnaWave VPN Shop Bot

Современный Telegram бот для продажи VPN подписок с интеграцией RemnaWave API.

## 🚀 Особенности

- **Полная интеграция с RemnaWave API** - современная панель управления VPN
- **Автоматическое управление пользователями** - создание, продление, блокировка
- **Гибкая система тарифов** - настраиваемые планы и цены
- **Множественные способы оплаты** - Telegram Stars, Cryptomus, YooKassa и др.
- **Реферальная система** - двухуровневая система вознаграждений
- **Пробный период** - бесплатные тестовые подписки
- **Админ-панель** - полное управление через Telegram
- **Мониторинг и статистика** - детальная аналитика использования

## 🏗️ Архитектура

### Основные компоненты

- **RemnavaveApiClient** - базовый клиент для работы с RemnaWave API
- **RemnavaveVPNService** - сервис управления VPN пользователями
- **RemnavaveEnhancedService** - расширенные возможности и статистика
- **RemnavaveServerPoolService** - управление пулом серверов

### Технологии

- **Python 3.8+** - основной язык разработки
- **aiogram 3.x** - современный фреймворк для Telegram ботов
- **SQLAlchemy 2.x** - ORM для работы с базой данных
- **Redis** - кэширование и сессии
- **PostgreSQL** - основная база данных
- **Docker** - контейнеризация и развертывание

## 📋 Требования

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- RemnaWave панель v2.15+
- Доступ к Telegram Bot API

## 🛠️ Установка

### Быстрая установка

```bash
# Клонирование репозитория
git clone <your-repo-url>
cd remnawave-vpn-bot

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Запуск тестов
python test_remnawave_api.py

# Запуск бота
python -m app
```

### Docker установка

```bash
# Запуск через docker-compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
```

## ⚙️ Конфигурация

### Основные переменные окружения

```bash
# RemnaWave API
REMNAWAVE_USERNAME=your_admin_username
REMNAWAVE_PASSWORD=your_admin_password
REMNAWAVE_API_URL=https://your-panel.com
REMNAWAVE_SUBSCRIPTION_PATH=/sub

# Telegram Bot
BOT_TOKEN=your_bot_token
BOT_ADMINS=123456789,987654321
BOT_DOMAIN=your-domain.com

# База данных
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=bot_user
DB_PASSWORD=your_password
DB_NAME=bot_database
```

### Настройка планов

Отредактируйте `plans.json`:

```json
{
    "durations": [30, 60, 180, 365],
    "plans": [
        {
            "devices": 1,
            "prices": {
                "RUB": {"30": 100, "60": 180, "180": 450, "365": 800},
                "USD": {"30": 1.0, "60": 1.8, "180": 4.5, "365": 8.0}
            }
        }
    ]
}
```

## 🔧 Использование

### Основные команды бота

- `/start` - начало работы с ботом
- `/buy` - покупка подписки
- `/profile` - профиль пользователя
- `/referral` - реферальная система
- `/support` - поддержка

### Админ команды

- `/admin` - админ-панель
- `/stats` - статистика системы
- `/users` - управление пользователями
- `/servers` - управление серверами
- `/notifications` - отправка уведомлений

## 📊 API интеграция

### Создание пользователя

```python
from app.bot.services.remnawave_vpn import RemnavaveVPNService

# Создание нового клиента
success = await vpn_service.create_client(
    user=user,
    devices=3,
    duration=30,
    traffic_limit_gb=10,
    traffic_reset_strategy="MONTH"
)
```

### Получение статистики

```python
from app.bot.services.remnawave_enhanced import RemnavaveEnhancedService

# Системная статистика
stats = await enhanced_service.get_system_statistics()
print(f"Пользователей: {stats['users']['total']}")
print(f"Узлов: {stats['nodes']['total']}")
```

### Управление узлами

```python
from app.bot.services.remnawave_server_pool import RemnavaveServerPoolService

# Синхронизация узлов
await server_pool.sync_nodes()

# Получение лучшего узла
best_node = await server_pool.get_best_node(criteria="latency")
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Тестирование API интеграции
python test_remnawave_api.py

# Запуск unit тестов
pytest tests/

# Проверка кода
black app/
isort app/
flake8 app/
mypy app/
```

### Тестовые сценарии

- Подключение к RemnaWave API
- Создание и управление пользователями
- Работа с подписками
- Мониторинг узлов
- Системная статистика

## 📈 Мониторинг

### Логирование

Все операции логируются с различными уровнями:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Операция выполнена успешно")
logger.error("Произошла ошибка")
logger.debug("Детальная информация")
```

### Метрики

- Количество активных пользователей
- Статус узлов серверов
- Использование трафика
- Время отклика API

## 🔒 Безопасность

- Аутентификация через JWT токены
- Автоматическое обновление токенов
- Валидация входных данных
- Логирование всех операций
- Ограничение доступа к админ-функциям

## 🚀 Развертывание

### Продакшен

```bash
# Сборка Docker образа
docker build -t remnawave-bot .

# Запуск с переменными окружения
docker run -d \
  --name remnawave-bot \
  --env-file .env \
  -p 8080:8080 \
  remnawave-bot
```

### Мониторинг

```bash
# Просмотр логов
docker logs -f remnawave-bot

# Статистика контейнера
docker stats remnawave-bot

# Перезапуск сервиса
docker restart remnawave-bot
```

## 📚 Документация

- [Руководство по установке](REMNARAVE_SETUP.md)
- [Использование API](REMNARAVE_API_USAGE.md)
- [Примеры кода](examples/)
- [API документация RemnaWave](remnawave-api-v215.yaml)

## 🤝 Поддержка

### Сообщество

- [Telegram канал](https://t.me/your_channel)
- [GitHub Issues](https://github.com/your-repo/issues)
- [Discord сервер](https://discord.gg/your_server)

### Разработка

- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Development Setup](DEVELOPMENT.md)

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- Команде RemnaWave за отличную панель управления
- Сообществу aiogram за фреймворк
- Всем контрибьюторам проекта

## 🔄 Обновления

### v1.0.0 (Текущая версия)

- ✅ Полная интеграция с RemnaWave API
- ✅ Система управления пользователями
- ✅ Автоматическое продление подписок
- ✅ Реферальная система
- ✅ Админ-панель
- ✅ Docker поддержка

### Планы развития

- [ ] Веб-интерфейс для администрирования
- [ ] Расширенная аналитика
- [ ] Интеграция с дополнительными платежными системами
- [ ] API для внешних интеграций
- [ ] Мобильное приложение

---

**⭐ Если проект вам понравился, поставьте звезду на GitHub!**
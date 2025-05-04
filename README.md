
# 🤖 Telegram-бот с платной подпиской для закрытого канала

Telegram-бот для автоматизации доступа в закрытый Telegram-клуб.  
Он принимает оплату, выдаёт доступ, отслеживает срок подписки, уведомляет об окончании и автоматически удаляет участников с истёкшим доступом.

---

## 🚀 Функциональность

- Команда `/start` с описанием и кнопкой оплаты
- Генерация платёжной ссылки через **YooMoney API**
- Проверка статуса платежа
- Выдача **одноразовой** ссылки-приглашения в канал
- Автоматическое добавление в базу после оплаты
- Ежедневная проверка подписок
- Напоминание за 2 дня до окончания доступа
- Автоматическое удаление из канала после окончания срока

---

## 🛠 Технологии

| Компонент         | Используется                  |
|-------------------|-------------------------------|
| Язык              | Python 3.11                   |
| Telegram API      | `aiogram 3.x`                 |
| Платёжная система | YooMoney API                  |
| База данных       | SQLite                        |
| Настройки         | `python-dotenv`               |
| Деплой            | VPS (Timeweb) + `systemd`     |

---

## 📁 Структура проекта

```
project/
├── bot_handlers.py         # Логика команд и клавиатур
├── config.py               # Переменные окружения и токены
├── db.py                   # Работа с базой данных
├── main.py                 # Точка входа в приложение
├── requirements.txt        # Список зависимостей
├── .env                    # Файл с конфигурацией (не пушить в Git)
└── data/
    └── subscriptions.db    # SQLite-база данных
```

---

## ⚙️ Установка

1. **Клонировать репозиторий:**

```bash
git clone https://github.com/yourusername/telegram-subscription-bot.git
cd telegram-subscription-bot
```

2. **Создать виртуальное окружение и установить зависимости:**

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Создать `.env` файл:**

```env
BOT_TOKEN=your_telegram_bot_token
YOOMONEY_TOKEN=your_yoomoney_api_key
YOOMONEY_WALLET=your_wallet_number
CHANNEL_ID=-100xxxxxxxxxx
DATABASE_PATH=data/subscriptions.db
SUB_PRICE=490.0
SUB_DURATION_DAYS=30
CHECK_INTERVAL=60
```

---

## 🖥️ Запуск вручную

```bash
python main.py
```

---

## 🔁 Автозапуск через systemd (VPS)

Создай файл:

```bash
sudo nano /etc/systemd/system/telegrambot.service
```

Добавь:

```ini
[Unit]
Description=Telegram Bot for Subscription Access
After=network.target

[Service]
User=root
WorkingDirectory=/root/bot/project
ExecStart=/root/bot/project/venv/bin/python /root/bot/project/main.py
EnvironmentFile=/root/bot/project/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

Запусти и включи:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable telegrambot
sudo systemctl start telegrambot
sudo journalctl -u telegrambot -f
```

---

## 🔐 Безопасность

- Все данные хранятся локально в SQLite
- Одноразовые ссылки в канал
- Защита от повторного доступа
- Все конфиденциальные данные вынесены в `.env` файл

---

## 📎 Полезные ссылки

- 🤖 Бот в Telegram: [@Circassiangirl_bot](https://t.me/Circassiangirl_bot)  
- 🛠 Репозиторий: [GitHub](https://github.com/yourusername/telegram-subscription-bot)

---

## 📬 Обратная связь

Если вы хотите аналогичного бота — напишите мне в [Telegram](https://t.me/your_username) или откройте Issue в репозитории.

---

## 📝 Лицензия

MIT License — свободное использование с указанием авторства.

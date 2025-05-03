# main.py
import asyncio
from aiogram import Bot, Dispatcher
import logging

import config
from db import (
    init_db,
    get_pending_payments,
    mark_payment_success,
    add_or_update_subscription,
)
from db import get_expired_subscriptions, remove_subscription
from bot_handlers import router

from yoomoney import Client

import sqlite3
from datetime import datetime

import requests
from aiogram.exceptions import TelegramBadRequest

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Инициализация
init_db()
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)
yoo_client = Client(token=config.YOOMONEY_TOKEN)


async def payment_checker():
    """Фоновая задача: каждые CHECK_INTERVAL сек проверяем status pending."""
    while True:
        pendings = get_pending_payments()
        for p in pendings:
            label = p["label"]
            user_id = p["user_id"]
            try:
                # ищем историю операций по метке
                history = yoo_client.operation_history(label=label)
                for op in history.operations:
                    if getattr(op, "status", None) == "success":
                        # помечаем платёж, активируем подписку и шлём ссылку
                        mark_payment_success(label, op.operation_id)
                        add_or_update_subscription(user_id)
                        # разовая пригласительная ссылка
                        link = await bot.create_chat_invite_link(
                            chat_id=config.CHANNEL_ID, member_limit=1
                        )
                        await bot.send_message(
                            user_id,
                            (
                                "✅ Оплата принята, твоя подписка активирована!\n"
                                f"Вступай в канал по ссылке:\n{link.invite_link}\n"
                                "Нажми /start, чтобы продлить или посмотреть статус подписки"
                            ),
                        )
                        logging.info(f"Пользователь {user_id} оплатил, ссылка выдана.")
                        break
            except requests.exceptions.RequestException as e:
                logging.warning(
                    f"[payment_checker] Ошибка сети при проверке {label}: {e}"
                )
        await asyncio.sleep(config.CHECK_INTERVAL)


async def subscription_cleaner():
    """Фоновая задача: раз в час удаляем просроченные подписки."""
    while True:
        expired = get_expired_subscriptions()
        for uid in expired:
            try:
                # бан+разбан = удаление из канала
                await bot.ban_chat_member(config.CHANNEL_ID, uid)
                await bot.unban_chat_member(config.CHANNEL_ID, uid)
                remove_subscription(uid)
                await bot.send_message(
                    uid, "⏰ Ваша подписка истекла. Чтобы продлить — /start"
                )
                logging.info(f"Подписка у {uid} завершена, удалён из канала.")
            except TelegramBadRequest as e:
                logging.warning(
                    f"[subscription_cleaner] TelegramBadRequest для {uid}: {e}"
                )
        await asyncio.sleep(3600)


# --- Reminder task ---
async def reminder_task():
    """Каждый час напоминаем за 2 дня до окончания подписки."""
    while True:
        now_ts = int(datetime.now().timestamp())
        two_days = 2 * 24 * 3600
        conn = sqlite3.connect(config.DATABASE_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user_id, end_ts
            FROM subscriptions
            WHERE reminded=0
              AND end_ts > ?
              AND end_ts <= ?
            """,
            (now_ts, now_ts + two_days),
        )
        rows = cur.fetchall()
        for user_id, end_ts in rows:
            end_date = datetime.fromtimestamp(end_ts).strftime("%d.%m.%Y %H:%M")
            try:
                await bot.send_message(
                    user_id,
                    f"⚠️ Ваша подписка истекает {end_date} — осталось меньше 2 дней.\n"
                    "Чтобы не потерять доступ, продлите её командой /start",
                )
            except TelegramBadRequest:
                pass
            cur.execute(
                "UPDATE subscriptions SET reminded=1 WHERE user_id = ?", (user_id,)
            )
        conn.commit()
        conn.close()
        await asyncio.sleep(3600)


async def main():
    # запускаем фоновые задачи
    asyncio.create_task(payment_checker())
    asyncio.create_task(subscription_cleaner())
    asyncio.create_task(reminder_task())
    # стартуем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

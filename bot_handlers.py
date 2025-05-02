# bot_handlers.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import uuid

import config
from db import get_subscription, add_payment

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    sub = get_subscription(user_id)
    if sub and sub["end_ts"] > int(__import__("time").time()):
        from datetime import datetime

        end = datetime.fromtimestamp(sub["end_ts"]).strftime("%d.%m.%Y %H:%M")
        await message.answer(f"✅ Ваша подписка активна до {end}.")
        return

    # Если подписки нет или она истекла
    await message.answer(
        f"👋 Привет! Подписка на канал:\n"
        f"• Стоимость: {config.SUB_PRICE} ₽\n"
        f"• Длительность: {config.SUB_DURATION_DAYS} дней\n\n"
        "Нажми кнопку ниже, чтобы оплатить."
    )
    # генерируем уникальную метку
    label = f"{user_id}_{uuid.uuid4().hex}"
    # создаем ссылку YooMoney
    from yoomoney import Quickpay

    qp = Quickpay(
        receiver=config.YOOMONEY_WALLET,
        quickpay_form="shop",
        targets="Оплата подписки",
        paymentType="AC",
        sum=config.SUB_PRICE,
        label=label,
    )
    pay_url = qp.base_url
    # сохраняем платёж
    add_payment(user_id, label, config.SUB_PRICE)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Оплатить ₽", url=pay_url)]]
    )
    await message.answer("Перейди по ссылке для оплаты:", reply_markup=kb)

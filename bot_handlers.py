from aiogram import Router, types
from yoomoney import Quickpay
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import uuid
import time
from aiogram.exceptions import TelegramBadRequest

import config
from db import get_subscription, add_payment

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    sub = get_subscription(user_id)
    from datetime import datetime

    if sub and sub["end_ts"] > int(time.time()):
        end = datetime.fromtimestamp(sub["end_ts"]).strftime("%d.%m.%Y %H:%M")
        text = f"✅ Ваша подписка активна до {end}.\n\nХотите продлить подписку?"
        button_text = "Продлить ₽"
    else:
        text = (
            f"👋 Привет! Подписка на канал:\n"
            f"• Стоимость: {config.SUB_PRICE} ₽\n"
            f"• Длительность: {config.SUB_DURATION_DAYS} дней\n\n"
            "Нажми кнопку ниже, чтобы оплатить"
        )
        button_text = "Оплатить ₽"
    await message.answer(text)
    # генерируем уникальную метку
    label = f"{user_id}_{uuid.uuid4().hex}"
    # создаем ссылку YooMoney

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
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📆 Статус подписки", callback_data="subscription_status"
                )
            ],
            [InlineKeyboardButton(text=button_text, url=pay_url)],
        ]
    )
    await message.answer("Выберите действие:", reply_markup=kb)


# Handler to check bot's rights in the channel
@router.message(Command("check_rights"))
async def cmd_check_rights(message: types.Message):
    bot_user = await message.bot.get_me()
    info = await message.bot.get_chat_member(
        chat_id=config.CHANNEL_ID, user_id=bot_user.id
    )
    can_ban = getattr(info, "can_restrict_members", False)
    can_invite = getattr(info, "can_invite_users", False)
    await message.answer(
        f"Права бота в канале:\n"
        f"• Может удалять (ban): {can_ban}\n"
        f"• Может приглашать: {can_invite}"
    )


# Test handler to ban and unban the invoking user (self-test)
@router.message(Command("test_kick"))
async def cmd_test_kick(message: types.Message):
    user_id = message.from_user.id
    try:
        # Ban and immediately unban to remove from channel
        await message.bot.ban_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        await message.bot.unban_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        await message.answer(
            "✅ Тестовое удаление выполнено, вы удалены и восстановлены в канале."
        )
    except TelegramBadRequest as e:
        # If user is admin, cannot ban
        if "administrator" in e.message.lower():
            await message.answer("⚠️ Невозможно удалить администратора канала.")
        else:
            await message.answer(f"Ошибка при попытке удаления: {e.message}")


@router.callback_query(lambda c: c.data == "subscription_status")
async def cb_subscription_status(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sub = get_subscription(user_id)
    from datetime import datetime

    if sub and sub["end_ts"] > int(time.time()):
        end = datetime.fromtimestamp(sub["end_ts"]).strftime("%d.%m.%Y %H:%M")
        text = f"✅ Ваша подписка активна до {end}.\n\nХотите продлить подписку?"
        button_text = "Продлить ₽"
    else:
        text = (
            f"👋 У вас нет активной подписки.\n"
            f"• Стоимость: {config.SUB_PRICE} ₽\n"
            f"• Длительность: {config.SUB_DURATION_DAYS} дней\n\n"
            "Нажми кнопку ниже, чтобы оплатить"
        )
        button_text = "Оплатить ₽"
    # генерируем новую ссылку для оплаты
    label = f"{user_id}_{uuid.uuid4().hex}"
    qp = Quickpay(
        receiver=config.YOOMONEY_WALLET,
        quickpay_form="shop",
        targets="Оплата подписки",
        paymentType="AC",
        sum=config.SUB_PRICE,
        label=label,
    )
    pay_url = qp.base_url
    add_payment(user_id, label, config.SUB_PRICE)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=button_text, url=pay_url)]]
    )
    await callback.message.edit_text(text, reply_markup=kb)

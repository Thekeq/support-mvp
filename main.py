import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv
from db import DataBase
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Если забыли установить ключ бота
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не установлен в .env")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
router = Router()
db = DataBase("data.db")


@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    if not db.user_admin(user_id):
        await message.reply("Напишите свое сообщение и мы ответим на него в кротчайший срок!")
    else:
        await message.reply(f"Здравствуйте {name}! В ожидании сообщений :)")


@router.message(lambda msg: msg.text and msg.text.startswith("+"))
async def add(message: Message):
    user_id = message.from_user.id

    if db.user_admin(user_id):
        id = message.text[::1]
        db.add_user(id)

    elif not db.get_admins():
        db.add_user(user_id)


@router.message(StateFilter(None), F.text)
async def get_message(message: Message):
    user_id = message.from_user.id
    admins = db.get_admins()

    # Если пользователь НЕ админ и НЕ заблокирован
    if not db.user_admin(user_id) and user_id not in db.users_banned():
        try:
            username = f"@{message.from_user.username}"
        except:
            username = f"{message.from_user.full_name}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ответить",
                    callback_data=f"reply:{user_id}"
                ),
                InlineKeyboardButton(
                    text="Заблокировать",
                    callback_data=f"block:{user_id}"
                )
            ]
        ])

        # Отправка всем админам
        for admin_id in admins:
            await bot.send_message(
                admin_id,
                f"{message.text}\n\nСообщение от {username}, ID: {user_id}",
                reply_markup=keyboard
            )

    # Если пользователь заблокирован
    elif user_id in db.users_banned():
        await message.reply("Вы были заблокированы в боте! ❌")


class ReplyState(StatesGroup):
    waiting_for_reply = State()


@router.callback_query(F.data.startswith("reply:"))
async def handle_reply(callback: CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split(":")[1])

    await state.update_data(target_user_id=target_user_id)
    await callback.message.answer("Введите сообщение для ответа пользователю:")

    # Устанавливаем состояние
    await state.set_state(ReplyState.waiting_for_reply)

    await callback.answer()


@router.message(ReplyState.waiting_for_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    # Отправляем сообщение пользователю
    try:
        await bot.send_message(target_user_id, f"<b>Ответ от администратора:</b>\n\n{message.text}")
        await message.answer("✅ Ответ отправлен.")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение. {e}")

    await state.clear()


@router.callback_query(F.data.startswith("block:"))
async def handle_block(callback: CallbackQuery):
    target_user_id = int(callback.data.split(":")[1])

    # Блокировка, оповещение, что блокировка успешна
    db.ban(target_user_id)
    await callback.message.answer(f"Пользователь {target_user_id} заблокирован ✅")

    await callback.answer()


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    print("Telegram Bot is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

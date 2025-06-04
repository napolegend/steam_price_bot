from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.database import add_user, DB_PATH, get_all_command_stats, is_admin
import logging
import sqlite3

router = Router()
@router.message(Command("start"))
async def start_command(message: Message):
    add_user(message.from_user.id)
    await message.answer("Привет! Я бот для отслеживания цен на игры и DLC в steam\n"
                         "/help - подробнее про команды"
                         "Алё алё игры да да деньги")

    logging.info(f"User {message.from_user.id} called /start")

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("Список команд бота: \n"
                         "/start - запустить бота \n"
                         "/help - отобразить это меню \n"
                         "/subscribe подписаться на оповещение при снижении цены на игру / DLC с определенным id до уровня price в рублях \n"
                         "/unsubscribe - отписаться от уведомления \n"
                         "/list - посмотреть свои заявки"
                         "/edit - изменить цену \n\n"
                         "ℹ️ Как использовать бота:\n\n"
                         "1. Найти ID игры в Steam (в URL страницы игры)\n"
                         "   Пример: https://store.steampowered.com/app/730/CounterStrike_2/\n"
                         "   ID игры: 730\n\n"
                         "2. Добавить отслеживание: /subscribe\n"
                         "3. Указать ID игры и желаемую цену\n\n"
                         "📣 Бот будет уведомлять вас, когда цена опустится ниже указанной!"
                         )

    logging.info(f"User {message.from_user.id} called /help")

@router.message(Command("stats"))
async def stats_command(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("У вас нет прав для использования этой команды.")
        return

    # Если пользователь админ — получаем статистику
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    conn.close()

    stats = get_all_command_stats()
    if not stats:
        await message.answer("📊 Статистика пока пуста.")
        return

    reply = ["📊 Статистика по командам:"]
    for cmd, count in stats:
        reply.append(f"{cmd} — {count}")

    await message.answer("\n".join(reply))
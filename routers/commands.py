from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.database import add_user, DB_PATH, get_all_command_stats, is_admin, ADMINS
import logging
import sqlite3

router = Router()
@router.message(Command("start"))
async def start_command(message: Message):
    add_user(message.from_user.id)
    await message.answer("Привет! Я бот для отслеживания цен на игры и DLC в steam\n"
                         "/help - подробнее про команды\n"
                         "Алё алё игры да да деньги")

    logging.info(f"User {message.from_user.id} called /start")

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("Список команд бота: \n"
                         "/start - запустить бота \n"
                         "/help - отобразить это меню \n"
                         "/subscribe подписаться на оповещение при снижении цены на игру / DLC с определенным id до уровня price в рублях \n"
                         "/unsubscribe - отписаться от уведомления \n"
                         "/list - посмотреть свои заявки\n"
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

@router.message(Command("ban"))
async def ban_command(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.answer("❌ У вас нет прав использовать эту команду.")
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("❌ Используйте: /ban <id_user>")
        return

    target_user_id = int(args[1])

    if target_user_id in ADMINS:
        await message.answer("❌ Нельзя забанить администратора.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE id = ?", (target_user_id,))
    if c.fetchone() is None:
        c.execute("INSERT INTO users (id, is_banned) VALUES (?, 1)", (target_user_id,))
    else:
        c.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (target_user_id,))
    conn.commit()
    conn.close()

    await message.answer(f"✅ Пользователь с ID {target_user_id} забанен.")

@router.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("У вас нет прав для этой команды.")
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /unban <user_id>")
        return

    user_id = int(parts[1])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    await message.answer(f"Пользователь {user_id} разбанен.")


import os
from aiogram import Router, Bot
from aiogram.types import Message, BotCommand, BotCommandScopeDefault
from aiogram.filters import Command
from services.database import add_user, DB_PATH, get_all_command_stats, is_admin, ADMINS
import logging
import sqlite3

bot = Bot(os.getenv("TOKEN"))
router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    add_user(message.from_user.id)

    if message.from_user.id not in ADMINS:
        await message.answer("😇 Привет! Я бот для отслеживания цен на игры и DLC в steam\n"
                             "/help - подробнее про команды\n"
                             "Алё алё игры да да деньги 💰")
    else:
        await message.answer("😇 Привет! Я бот для отслеживания цен на игры и DLC в steam\n"
                             "/help - подробнее про команды\n"
                             "ЗДЕСЬ У ТЕБЯ ЕСТЬ ВЛАСТЬ ГОРДИСЬ ЭТИМ!!! 🤟")

    logging.info(f"User {message.from_user.id} called /start")

@router.message(Command("help"))
async def help_command(message: Message):
    if message.from_user.id in ADMINS:
        cmd_menu = [BotCommand(command='start', description='запустить бота'),
                    BotCommand(command='help', description='запустить меню помощи'),
                    BotCommand(command='subscribe', description='подписаться на оповещение'),
                    BotCommand(command='unsubscribe', description='отписаться от оповещения'),
                    BotCommand(command='list', description='посмотреть свои заявки'),
                    BotCommand(command='edit', description='изменить цену оповещения'),
                    BotCommand(command='ban', description='забанить пользователя по тг id'),
                    BotCommand(command='unban', description='разбанить пользователя по тг id'),
                    BotCommand(command='stats', description='посмотреть статистику бота'), ]
        await message.answer("🔎 Список общих команд бота: \n"
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
                             "📣 Бот будет уведомлять вас, когда цена опустится ниже указанной!\n\n"
                             "❓ Возможности для админа:\n"
                             "/stats - посмотреть статистику по введенным командам\n"
                             "/ban - забанить пользователя\n"
                             "/unban - разбанить пользователя"
                             )
        await bot.set_my_commands(cmd_menu, BotCommandScopeDefault())
    else:
        await message.answer("🔎 Список команд бота: \n"
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
        cmd_menu = [BotCommand(command='start', description='запустить бота'),
                    BotCommand(command='help', description='запустить меню помощи'),
                    BotCommand(command='subscribe', description='подписаться на оповещение'),
                    BotCommand(command='unsubscribe', description='отписаться от оповещения'),
                    BotCommand(command='list', description='посмотреть свои заявки'),
                    BotCommand(command='edit', description='изменить цену оповещения'), ]
        await bot.set_my_commands(cmd_menu, BotCommandScopeDefault())

    logging.info(f"User {message.from_user.id} called /help")

@router.message(Command("stats"))
async def stats_command(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав для использования этой команды.")
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

    logging.info(f"User {message.from_user.id} called /stats")

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

    logging.info(f"User {message.from_user.id} called /ban")

@router.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("❌ Используйте: /unban <user_id>")
        return

    user_id = int(parts[1])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    await message.answer(f"✅ Пользователь с ID {user_id} разбанен.")

    logging.info(f"User {message.from_user.id} called /unban")


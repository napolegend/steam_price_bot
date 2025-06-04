from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.database import add_user
import logging

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
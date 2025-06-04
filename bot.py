import os
import logging
import asyncio

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.fsm.storage.memory import MemoryStorage


from routers import commands, tracking
from services.database import get_trackings, add_price, delete_tracking_by_id
from services.steam import get_game_info

load_dotenv()
# 1) Конфигурируем корневой логгер
logger = logging.getLogger()              # корневой логгер
logger.setLevel(logging.INFO)             # уровень логирования

# 2) Хэндлер для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_fmt = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    "%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(console_fmt)
logger.addHandler(console_handler)

# 3) Хэндлер для записи в файл
file_handler = logging.FileHandler("bot.log", encoding="utf-8", mode="a")
file_handler.setLevel(logging.INFO)
file_fmt = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    "%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_fmt)
logger.addHandler(file_handler)

# Каждый час собирает данные по ценам и рассылает уведомления
async def check_prices(bot: Bot):
    while True:
        try:
            trackings = get_trackings()
            for t in trackings:
                tracking_id, user_id, game_id, game_name, threshold, created_at = t
                game_info = get_game_info(game_id)

                # Пропускаем если цена недоступна
                if game_info["price"] is None:
                    continue

                current_price = game_info["price"]
                add_price(game_id, current_price)



                # Если цена опустилась ниже порога и изменилась
                # P.S. увеличение на 15% обусловлено "жадностью" и последующим сожалением некоторых пользователей :)
                if current_price <= 1.15 * threshold:
                    # Форматирование сообщения для бесплатных игр
                    price_msg = f"{current_price} руб."

                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🔥 Цена опустилась!\n\n"
                             f"🎮 {game_name}\n"
                             f"💰 Новая цена: {price_msg}\n"
                             f"🔔 Ваш порог: {threshold} руб."
                    )
                    delete_tracking_by_id(tracking_id,user_id)
        except Exception as e:
            logging.error(f"Price check error: {e}")

        await asyncio.sleep(360)


async def main():
    bot = Bot(os.getenv("TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_router(commands.router)
    dp.include_router(tracking.router)

    cmd_menu = [BotCommand(command='start', description='запустить бота'),
                    BotCommand(command='help', description='запустить меню помощи'),
                    BotCommand(command='subscribe', description='подписаться на оповещение'),
                    BotCommand(command='unsubscribe', description='отписаться от оповещения'),
                    BotCommand(command='list', description='посмотреть свои заявки'),
                    BotCommand(command='edit', description='изменить цену оповещения'),]
    await bot.set_my_commands(cmd_menu, BotCommandScopeDefault())
    print("Bot is running...")
    asyncio.create_task(check_prices(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.info("Starting bot...")
    asyncio.run(main())



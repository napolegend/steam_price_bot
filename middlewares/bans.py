import sqlite3
import os
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any

from services.database import DB_PATH

admin_env = os.getenv("ADMINS", "")
ADMINS = [int(admin_id) for admin_id in admin_env.split(",") if admin_id.strip().isdigit()]

# Примерный список матов
BAD_WORDS = ["шлюха", "идиот", "блядь", "сука", "хуесос", "долбоеб", "мразь",
             "уебок", "пидор", "пидорас", "конченный", "придурок", "пошел нахуй",
             "аутист", "уебище", "сын помойной бляди", "блядина", "скотина"] # Потом пополним


class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Any],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        text = event.text.lower() if event.text else ""

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT is_banned FROM users WHERE id = ?", (user_id,))
        result = c.fetchone()

        if result and result[0] == 1:
            await event.answer("Вы заблокированы за нарушение правил womp-womp")
            conn.close()
            return

        # Проверка на маты
        if any(bad_word in text for bad_word in BAD_WORDS):
            if user_id not in ADMINS:
                c.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (user_id,))
                conn.commit()
                await event.answer("Вы были забанены за нарушение правил womp-womp")
                conn.close()
                return
            else:
                await event.answer("Окак...")
        conn.close()

        return await handler(event, data)


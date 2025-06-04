from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def catch_all_handler(message: Message):
    pass

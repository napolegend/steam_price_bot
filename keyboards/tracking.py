from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.database import get_user_trackings_for_keyboard


def create_tracking_keyboard(user_id: int, action: str) -> InlineKeyboardMarkup | None:
    """
    Создает инлайн-клавиатуру для выбора отслеживания
    :param user_id: ID пользователя
    :param action: Действие ('delete' или 'edit')
    :return: Объект клавиатуры или None
    """
    trackings = get_user_trackings_for_keyboard(user_id)

    if not trackings:
        return None

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for tracking in trackings:
        # Форматируем текст кнопки
        button_text = f"{tracking['name']} (до {tracking['threshold']} руб.)"
        if len(button_text) > 40:
            button_text = button_text[:37] + "..."

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"{action}_{tracking['id']}"
            )
        ])

    return keyboard

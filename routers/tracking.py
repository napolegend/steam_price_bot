from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.tracking_states import AddTracking, EditTracking
from services.database import add_user, add_tracking, get_user_trackings, get_user_trackings_for_keyboard, \
    delete_tracking_by_id, get_user, update_tracking_threshold
from services.steam import get_game_info
from keyboards.tracking import create_tracking_keyboard

router = Router()


@router.message(Command("subscribe"))
async def start_add_tracking(message: types.Message, state: FSMContext):
    await message.answer("🔎 Введите ID игры в Steam:")
    await state.set_state(AddTracking.game_id)


@router.message(AddTracking.game_id, F.text.isdigit())
async def process_game_id(message: types.Message, state: FSMContext):
    game_id = int(message.text)
    game_info = get_game_info(game_id)
    user_id = add_user(message.from_user.id)
    trackings = get_user_trackings(user_id)
    for tracking in trackings:
        if tracking[2] == game_id:
            await message.answer("❌ У вас уже есть заявка на эту игру. Измените ее либо удалите.")
            await state.clear()
            return
    if not game_info or not game_info.get("name"):
        await message.answer("❌ Игра не найдена. Проверьте ID и попробуйте снова.")
        await state.clear()
        return

    # Обработка бесплатной игры
    if game_info["is_free"]:
        await message.answer(
            f"🎮 Игра: {game_info['name']}\n"
            f"💰 Цена: Бесплатно\n\n"
            "❌ Невозможно отслеживать цену бесплатной игры",
        )
        await state.clear()
        return

    # Проверка наличия цены
    if game_info["price"] is None:
        await message.answer(
            f"🎮 Игра: {game_info['name']}\n"
            "❌ Не удалось получить информацию о цене. Возможно, игра еще не вышла или недоступна в РФ.",
           
        )
        await state.clear()
        return

    await state.update_data(game_id=game_id, game_name=game_info["name"])
    await message.answer(
        f"🎮 Игра: {game_info['name']}\n"
        f"💰 Текущая цена: {game_info['price']} руб.\n\n"
        "🔎 Введите пороговую цену (в рублях):"
    )
    await state.set_state(AddTracking.threshold)


@router.message(AddTracking.threshold)
async def process_threshold(message: types.Message, state: FSMContext):
    try:
        threshold = float(message.text.replace(',', '.'))
        data = await state.get_data()

        user_id = add_user(message.from_user.id)
        add_tracking(
            user_id=user_id,
            game_id=data["game_id"],
            game_name=data["game_name"],
            threshold=threshold
        )

        await message.answer(
            f"✅ Отслеживание добавлено!\n\n"
            f"🎮 {data['game_name']}\n"
            f"🔔 Уведомление при цене ниже: {threshold} руб.",
        )
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число (например: 499.99)")
        return
    finally:
        await state.clear()


@router.message(Command("list"))
async def list_trackings(message: types.Message):
    user_id = add_user(message.from_user.id)
    trackings = get_user_trackings(user_id)

    if not trackings:
        await message.answer("📭 У вас нет активных отслеживаний")
        return

    response = ["📋 Ваши отслеживания:"]
    for tracking in trackings:
        response.append(
            f"\n🎮 {tracking[3]} (ID: {tracking[2]})\n"
            f"🔔 Уведомление при: {tracking[4]} руб.\n"
            f"🆔 ID отслеживания: {tracking[0]}"
        )

    await message.answer("\n".join(response),)


@router.message(Command("unsubscribe"))
async def delete_tracking_start(message: types.Message):
    user_id = add_user(message.from_user.id)
    keyboard = create_tracking_keyboard(user_id, action="delete")

    if not keyboard:
        await message.answer("📭 У вас нет активных отслеживаний")
        return

    await message.answer(
        "🔎 Выберите отслеживание для удаления:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("delete_"))
async def process_tracking_deletion(callback: types.CallbackQuery):
    tracking_id = int(callback.data.split("_")[1])
    user_id = get_user(callback.from_user.id)

    if not user_id:
        await callback.answer("❌ Ошибка: пользователь не найден")
        return

    deleted = delete_tracking_by_id(tracking_id, user_id)

    if deleted:
        # Удаляем клавиатуру
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("✅ Отслеживание успешно удалено!")
    else:
        await callback.answer("❌ Не удалось удалить отслеживание. Возможно, оно уже было удалено.")

    await callback.answer()


@router.message(Command("edit"))
async def edit_tracking_start(message: types.Message):
    """
    Начало редактирования отслеживания - показ списка
    """
    user_id = add_user(message.from_user.id)
    keyboard = create_tracking_keyboard(user_id, "edit")

    if not keyboard:
        await message.answer("📭 У вас нет активных отслеживаний")
        return

    await message.answer(
        "🔎 Выберите отслеживание для изменения пороговой цены:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("edit_"))
async def start_edit_tracking(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработка выбора отслеживания для редактирования
    """
    tracking_id = int(callback.data.split("_")[1])

    # Сохраняем ID отслеживания в состоянии
    await state.set_state(EditTracking.new_threshold)
    await state.update_data(tracking_id=tracking_id)

    # Убираем клавиатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer("🔎 Введите новую пороговую цену (в рублях):")
    await callback.answer()


@router.message(EditTracking.new_threshold)
async def process_edit_threshold(message: types.Message, state: FSMContext):
    """
    Обработка новой пороговой цены
    """
    try:
        new_threshold = float(message.text.replace(',', '.'))
        data = await state.get_data()
        tracking_id = data["tracking_id"]
        user_id = get_user(message.from_user.id)

        # Обновляем порог в базе данных
        updated = update_tracking_threshold(tracking_id, user_id, new_threshold)

        if updated:
            await message.answer(f"✅ Пороговая цена успешно обновлена на {new_threshold} руб.")
        else:
            await message.answer(
                "❌ Не удалось обновить отслеживание. Возможно, оно было удалено или вы не являетесь владельцем.")
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число (например: 499.99)")
        return
    finally:
        await state.clear()
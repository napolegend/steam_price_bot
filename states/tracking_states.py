from aiogram.fsm.state import State, StatesGroup

class AddTracking(StatesGroup):
    game_id = State()
    threshold = State()

class EditTracking(StatesGroup):
    tracking_id = State()
    new_threshold = State()
from aiogram.dispatcher.filters.state import State, StatesGroup


class User(StatesGroup):
    phone_number = State()
    menu = State()


class MovementGrainOnElevator(StatesGroup):
    detailing = State()
    date1 = State()
    date2 = State()


class TotalLeftoversGrainOnElevator(StatesGroup):
    detailing = State()
    date1 = State()

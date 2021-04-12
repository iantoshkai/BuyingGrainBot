import asyncio
import logging
import requests
import json
import os
from datetime import datetime
from typing import Union

import states
import keyboards
import filters
import database
from aiocalendar import calendar_callback, create_calendar, process_calendar_selection

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor, exceptions
from aiogram.types import ContentTypes
from aiogram.types import CallbackQuery

with open('./app/config.json', 'r') as config_file:
    config = json.load(config_file)

config['db_name'] = os.environ['MONGODB_DATABASE']
config['db_host'] = os.environ['MONGODB_HOSTNAME']
config['db_username'] = os.environ['MONGODB_USERNAME']
config['db_password'] = os.environ['MONGODB_PASSWORD']

loop = asyncio.get_event_loop()

logging.basicConfig(filename='./app/bot.log', filemode='a',
                    format='%(asctime)s %(levelname)s:  %(name)s  - %(message)s',
                    level=logging.INFO)

bot = Bot(token=config['token'])
storage = MongoStorage(host=config['db_host'], port=config['db_port'], db_name=config['db_name'],
                       username=config['db_username'], password=config['db_password'])
dp = Dispatcher(bot, storage=storage)


async def on_startup(dp: Dispatcher):
    await database.create_db()


async def check_phone_number(user_id: Union[str, int], phone_number: Union[str, int]):
    if str(user_id) in ADMINS_LIST:
        return True
    headers = {'bot_name': 'BuyingGrain',
               'Authorization': TOKEN,
               'number': str(phone_number),
               'userID': str(user_id)}
    url = URL_CHECK_ACCESS
    request = requests.post(url=url,
                            headers=headers,
                            verify=False)
    logging.info(f'{request.status_code} checkAccess: {user_id} from {phone_number}')
    if request.status_code == 200:
        if request.text == 'true':
            return True
        elif request.text == 'false':
            return False
        else:
            logging.error(f'RequestError {request.status_code}, checkAccess, {request.text}')
            raise Exception('RequestError', f'{request.status_code}, {request.text}')
    else:
        logging.error(f'RequestError {request.status_code}, checkAccess, {request.text}')
        raise Exception('RequestError', f'{request.status_code}, {request.text}')


async def get_report(type_report: str, user_id: Union[str, int], detailing: str, date1: datetime,
                     date2: datetime = None):
    date1 = date1.strftime('%Y-%m-%dT00:00:00')
    if type_report == 'MovementGrainOnElevator':
        date2 = date2.strftime('%Y-%m-%dT23:59:59')
        headers = {'bot_name': 'BuyingGrain',
                   'Detailing': detailing,
                   'TypeReport': 'fd8e8940-710c-11eb-8170-000c29b9c276',
                   'date1': date1,
                   'date2': date2,
                   'Authorization': TOKEN,
                   'userID': str(user_id)}
        url = URL_GET_REPORT
        request = requests.post(url=url,
                                headers=headers,
                                verify=False)
        logging.info(f'{request.status_code} | {type_report} | {detailing} : {user_id} from {date1} to {date2}')
        if request.status_code == 200:
            return request.content
        else:
            logging.error(f'RequestError {user_id} {request.status_code}, {type_report},  {request.text}')
            raise Exception('RequestError', f'{user_id}, {type_report}, {request.status_code}, {request.text}')
    elif type_report == 'TotalLeftoversGrainOnElevator':
        headers = {'bot_name': 'BuyingGrain',
                   'Detailing': detailing,
                   'TypeReport': '05d04a61-711f-11eb-8170-000c29b9c276',
                   'date1': date1,
                   'Authorization': TOKEN,
                   'userID': str(user_id)}
        url = URL_GET_REPORT
        request = requests.post(url=url,
                                headers=headers,
                                verify=False)
        logging.info(f'{request.status_code} | {type_report} | {detailing} : {user_id} from {date1}')
        if request.status_code == 200:
            return request.content
        else:
            logging.error(f'RequestError {user_id} {request.status_code}, {type_report},  {request.text}')
            raise Exception('RequestError', f'{user_id}, {type_report}, {request.status_code}, {request.text}')


@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text='👋🏻')
    try:
        user = database.User.objects(_id=f'{message.chat.id}')[0]
        if await check_phone_number(user_id=user._id, phone_number=user.phone_number):
            await states.User.menu.set()
            await bot.send_message(chat_id=message.chat.id, text='Вкажіть тип звіту👇🏻', reply_markup=keyboards.menu())
        else:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Твій номер відсутній в базі😕\nВ доступі відмовлено⛔️')
    except IndexError:
        logging.info(f'NewUser: {message.from_user.full_name} - {message.chat.id} - {message.from_user.username}')
        await states.User.phone_number.set()
        await bot.send_message(message.chat.id,
                               "Оуу, бачу ти новенький😄\nДля реєстрації мені потрібен твій номер телефону👇🏻",
                               reply_markup=keyboards.phone_number_keyboard())
    except Exception as e:
        await bot.send_message(chat_id=message.chat.id, text='Упс, виникла помилка😥')
        logging.error(e)


@dp.message_handler(content_types='contact', state=states.User.phone_number)
async def contact(message: types.Message, state: FSMContext):
    if message.from_user.id == message.contact.user_id:
        phone_number = message.contact.phone_number.replace('+', '').replace('38', '')
        logging.info(f'{message.from_user.id} -  {phone_number}')
        if await check_phone_number(user_id=message.chat.id, phone_number=phone_number):
            user = database.User(_id=str(message.chat.id), username=message.from_user.username,
                                 name=message.from_user.full_name,
                                 phone_number=phone_number)
            user.save()
            await states.User.menu.set()
            await bot.send_message(chat_id=message.chat.id,
                                   text='Реєстрація пройшла успішно🥳\nВкажіть тип звіту👇🏻',
                                   reply_markup=keyboards.menu())

        else:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Твій номер відсутній в базі😕\nВ доступі відмовлено⛔️',
                                   reply_markup=keyboards.phone_number_keyboard())
    else:
        logging.warning(f'BadPhone: {message.chat.id} - {message.contact.phone_number}')
        await bot.send_message(message.chat.id, 'Це не твій номер телефону👿\nВідправ свій👇🏻',
                               reply_markup=keyboards.phone_number_keyboard())


@dp.message_handler(filters.Button('⬅️ Назад'), state='*')
async def back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == states.MovementGrainOnElevator.detailing.state:
        await states.User.menu.set()
        await bot.send_message(chat_id=message.chat.id, text='Вкажіть тип звіту👇🏻', reply_markup=keyboards.menu())
    elif current_state == states.MovementGrainOnElevator.date1.state:
        user_data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=user_data['calendar_message_id'])
        await states.MovementGrainOnElevator.detailing.set()
        await bot.send_message(chat_id=message.chat.id,
                               text='Вкажіть деталізацію ⤵️',
                               reply_markup=keyboards.detailing())
    elif current_state == states.MovementGrainOnElevator.date2.state:
        user_data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=user_data['calendar_message_id'])
        await states.MovementGrainOnElevator.date1.set()
        await state.update_data()
        await bot.send_message(chat_id=message.chat.id, text="👇🏻", reply_markup=keyboards.back())
        calendar_message_id = await bot.send_message(chat_id=message.chat.id,
                                                     text='Оберіть початкову дату:',
                                                     reply_markup=create_calendar())
        await state.update_data(calendar_message_id=calendar_message_id.message_id)
    elif current_state == states.TotalLeftoversGrainOnElevator.detailing.state:
        await states.User.menu.set()
        await bot.send_message(chat_id=message.chat.id, text='Вкажіть тип звіту👇🏻', reply_markup=keyboards.menu())
    elif current_state == states.TotalLeftoversGrainOnElevator.date1.state:
        user_data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=user_data['calendar_message_id'])
        await states.TotalLeftoversGrainOnElevator.detailing.set()
        await bot.send_message(chat_id=message.chat.id,
                               text='Вкажіть деталізацію ⤵️',
                               reply_markup=keyboards.detailing())


@dp.message_handler(filters.Button('🌾 Рух зерна по елеватору'), state=states.User.menu)
async def get_report_buying_in_storage(message: types.Message, state: FSMContext):
    user = database.User.objects(_id=f'{message.chat.id}')[0]
    if await check_phone_number(user_id=user._id, phone_number=user.phone_number):
        await states.MovementGrainOnElevator.detailing.set()
        await bot.send_message(chat_id=message.chat.id,
                               text='Вкажіть деталізацію ⤵️',
                               reply_markup=keyboards.detailing())

    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='Твій номер відсутній в базі😕\nВ доступі відмовлено⛔️',
                               reply_markup=keyboards.menu())


@dp.message_handler(content_types=ContentTypes.TEXT,
                    state=states.MovementGrainOnElevator.detailing)
async def get_report_buying_in_storage(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == '🗃 Загальна':
            data["detailing"] = '0'
        elif message.text == '🗂 По контрагентам':
            data["detailing"] = '1'
    await states.MovementGrainOnElevator.date1.set()
    await bot.send_message(chat_id=message.chat.id, text="👇🏻", reply_markup=keyboards.back())
    calendar_message_id = await bot.send_message(chat_id=message.chat.id,
                                                 text='Оберіть початкову дату:',
                                                 reply_markup=create_calendar())
    await state.update_data(calendar_message_id=calendar_message_id.message_id)


@dp.callback_query_handler(calendar_callback.filter(),
                           state=states.MovementGrainOnElevator.date1)
async def storage_date1(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await process_calendar_selection(callback_query, callback_data)
    if selected:
        async with state.proxy() as data:
            data["date1"] = date
            calendar_message_id = await callback_query.message.edit_text(
                text=f'Початкова дата: {data["date1"].strftime("%Y.%m.%d")}\n'
                     f'Тепер оберіть кінцеву дату:',
                reply_markup=create_calendar())
            await state.update_data(calendar_message_id=calendar_message_id.message_id)
            await states.MovementGrainOnElevator.date2.set()


@dp.callback_query_handler(calendar_callback.filter(),
                           state=states.MovementGrainOnElevator.date2)
async def storage_date2(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await process_calendar_selection(callback_query, callback_data)
    if selected:
        async with state.proxy() as data:
            data["date2"] = date
            await callback_query.message.edit_text(
                text=f'Початкова дата: {data["date1"].strftime("%Y.%m.%d")}\n'
                     f'Кінцева дата: {data["date2"].strftime("%Y.%m.%d")}')
            msg = await bot.send_message(chat_id=callback_query.message.chat.id, text='⏳',
                                         reply_markup=keyboards.back())
            try:
                result = await get_report(type_report='MovementGrainOnElevator',
                                          detailing=data['detailing'],
                                          user_id=callback_query.from_user.id,
                                          date1=data["date1"], date2=data["date2"])
                await states.User.menu.set()
                if data['detailing'] == '0':
                    filename = f'Рух_зерна' \
                               f'_{data["date1"].strftime("%Y%m%d")}' \
                               f'_{data["date2"].strftime("%Y%m%d")}_{data["detailing"]}.pdf'
                elif data['detailing'] == '1':
                    filename = f'Рух_зерна' \
                               f'_{data["date1"].strftime("%Y%m%d")}' \
                               f'_{data["date2"].strftime("%Y%m%d")}_{data["detailing"]}.pdf'

                await bot.send_document(chat_id=callback_query.message.chat.id,
                                        document=(filename, result),
                                        reply_markup=keyboards.menu())
                await msg.delete()
            except Exception as e:
                await msg.edit_text('Щось пішло не так😢\nСпробуй пізніше')
                logging.error(e)


@dp.message_handler(filters.Button('📦 Загальні залишки елеватора'), state=states.User.menu)
async def get_report_buying_in_storage(message: types.Message, state: FSMContext):
    user = database.User.objects(_id=f'{message.chat.id}')[0]
    if await check_phone_number(user_id=user._id, phone_number=user.phone_number):
        await states.TotalLeftoversGrainOnElevator.detailing.set()
        await bot.send_message(chat_id=message.chat.id,
                               text='Вкажіть деталізацію ⤵️',
                               reply_markup=keyboards.detailing())

    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='Твій номер відсутній в базі😕\nВ доступі відмовлено⛔️',
                               reply_markup=keyboards.menu())


@dp.message_handler(content_types=ContentTypes.TEXT,
                    state=states.TotalLeftoversGrainOnElevator.detailing)
async def get_report_buying_in_storage(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == '🗃 Загальна':
            data["detailing"] = '0'
        elif message.text == '🗂 По контрагентам':
            data["detailing"] = '1'
    await states.TotalLeftoversGrainOnElevator.date1.set()
    await bot.send_message(chat_id=message.chat.id, text="👇🏻", reply_markup=keyboards.back())
    calendar_message_id = await bot.send_message(chat_id=message.chat.id,
                                                 text='Оберіть дату:',
                                                 reply_markup=create_calendar())
    await state.update_data(calendar_message_id=calendar_message_id.message_id)


@dp.callback_query_handler(calendar_callback.filter(),
                           state=states.TotalLeftoversGrainOnElevator.date1)
async def storage_date2(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await process_calendar_selection(callback_query, callback_data)
    if selected:
        async with state.proxy() as data:
            data["date1"] = date
            await callback_query.message.edit_text(
                text=f'Обрана дата: {data["date1"].strftime("%Y.%m.%d")}')
            msg = await bot.send_message(chat_id=callback_query.message.chat.id, text='⏳',
                                         reply_markup=keyboards.back())
            try:
                result = await get_report(type_report='TotalLeftoversGrainOnElevator',
                                          detailing=data['detailing'],
                                          user_id=callback_query.from_user.id,
                                          date1=data["date1"])
                await states.User.menu.set()
                if data['detailing'] == '0':
                    filename = f'Загальні_залишки' \
                               f'_{data["date1"].strftime("%Y%m%d")}' \
                               f'_{data["detailing"]}.pdf'
                elif data['detailing'] == '1':
                    filename = f'Загальні_залишки' \
                               f'_{data["date1"].strftime("%Y%m%d")}' \
                               f'_{data["detailing"]}.pdf'

                await bot.send_document(chat_id=callback_query.message.chat.id,
                                        document=(filename, result),
                                        reply_markup=keyboards.menu())
                await msg.delete()
            except Exception as e:
                await msg.edit_text('Щось пішло не так😢\nСпробуй пізніше')
                logging.error(e)


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, on_startup=on_startup, skip_updates=True)

# -*- coding: utf-8 -*-

from aiogram import *
from config import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards import *
import asyncio
import nest_asyncio
from defs import *
import exchange_rates
import webbrowser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uuid
from requests import *


storage = MemoryStorage()
bot = Bot(token, parse_mode='HTML')
disp = Dispatcher(bot, storage=storage)


class RegisterStatesGroup(StatesGroup):
    await_nickname = State()
    await_password = State()


class TransferStatesGroup(StatesGroup):
    await_password = State()
    await_recipient = State()
    await_amount = State()
    await_comment = State()
    await_confirmation = State()


class ChangingMoneyStatesGroup(StatesGroup):
    await_password = State()
    await_exchange_option = State()
    await_amount = State()
    await_confirmation = State()


class ReplenishTheBalanceStatesGroup(StatesGroup):
    await_password = State()
    await_amount = State()
    await_confirmation = State()


class WithdrawMoneyStatesGroup(StatesGroup):
    await_password = State()
    await_amount = State()
    await_confirmation = State()


class BlockUserState(StatesGroup):
    block_user = State()


async def on_startup(_):
    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = 'CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, nickname VARCHAR(80), password VARCHAR(80), RUB DECIMAL(10, 4), USD DECIMAL(10, 4), EUR DECIMAL(10, 4))'

        cursor.execute(query)

        db.commit()


@disp.callback_query_handler(text='cancel', state='*')
async def cancel_operation(callback, state):
    bot_message = await bot.send_message(callback.message.chat.id, '<b>Операция отменена</b>')

    await state.finish()

    await asyncio.sleep(7)
    await bot_message.delete()


# регистрация


@disp.message_handler(commands=['start'])
async def start_bot(message):
    if not is_registered(message.from_user.id):
        bot_message = await bot.send_message(message.chat.id, '<b>Привет! Я бот, специализирующийся на работе с валютными операциями. Пройди короткую регистрацию, чтобы приступить к работе со мной!</b>', reply_markup=start_registration_ikb)

        await asyncio.sleep(7)
        await bot_message.delete()

    else:
        await bot.send_message(message.chat.id, '<b>И снова здравствуйте!</b>', reply_markup=main_menu_kb)

    await message.delete()


@disp.callback_query_handler(lambda callback: callback.data == 'start_reg', state=None)
async def start_registration(callback):
    bot_message = await bot.send_message(callback.message.chat.id, '<b>Для начала пришли мне свое виртуальное имя</b>')

    await RegisterStatesGroup.await_nickname.set()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=RegisterStatesGroup.await_nickname)
async def handle_nickname(message, state):
    async with state.proxy() as data_storage:
        data_storage['nickname'] = message.text

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT nickname FROM users WHERE nickname = "{message.text}"'

        same_nicknames = cursor.execute(query).fetchall()

        db.commit()

    if same_nicknames:
        bot_message = await bot.send_message(message.chat.id, '<b>Такой никнейм уже существует, попробуй ввести другой !</b>')

    else:
        bot_message = await bot.send_message(message.chat.id, '<b>Отлично, теперь пришли мне свой пароль. Он будет нужен для подтверждения всех операций на твоем аккаунте, никому его не сообщай !</b>')

        await RegisterStatesGroup.next()


    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=RegisterStatesGroup.await_password)
async def handle_password(message, state):
    async with state.proxy() as data_storage:
        data_storage['password'] = message.text
        data_storage['user_id'] = message.from_user.id

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT password FROM users WHERE password = "{message.text}"'

        same_passwords = cursor.execute(query).fetchall()

        db.commit()


    if same_passwords:
        bot_message = await bot.send_message(message.chat.id, '<b>Такой пароль уже существует, попробуй ввести другой !</b>')

        await asyncio.sleep(7)
        await bot_message.delete()


    else:
        loop = asyncio.get_event_loop()

        nest_asyncio.apply()
        entering_status = loop.run_until_complete(entering_into_the_database(state))

        if entering_status:
            await bot.send_message(message.chat.id, '<b>Поздравляю, ты успешно создал свой аккаунт !!! Теперь тебе доступен весь функционал бота</b>', reply_markup=main_menu_kb)

        else:
            bot_message = await bot.send_message(message.chat.id, '<b>Ууупс, что-то пошло не так (. Попробуй зарегестрироваться заново или обратись в службу поддержки https://t.me/ThisIsMyShadow</b>')

            await asyncio.sleep(7)
            await bot_message.delete()

        await state.finish()

    await message.delete()


# просмотр курса валют


@disp.message_handler(text='Посмотреть курсы валют', state='*')
async def show_exchange_rate(message):
    bot_message = await bot.send_message(message.chat.id, f'<b>'
                                            f'▪️1 USD = {exchange_rates.currency_courses_data.dollar_to_rub_course} RUB\n'
                                            f'▪️1 RUB = {exchange_rates.currency_courses_data.rub_to_dollar_course} USD\n'
                                            f'▪️1 EUR = {exchange_rates.currency_courses_data.eur_to_rub_course} RUB\n'
                                            f'▪️1 RUB = {exchange_rates.currency_courses_data.rub_to_eur_course} EUR\n'
                                            f'▪️1 USD = {exchange_rates.currency_courses_data.dollar_to_eur_course} EUR\n'
                                            f'▪️1 EUR = {exchange_rates.currency_courses_data.eur_to_dollar_course} USD</b>')

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


# показ профиля


@disp.message_handler(text='Показать профиль', state='*')
async def show_user_profile(message):
    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT nickname, RUB, USD, EUR FROM users WHERE user_id = "{message.from_user.id}"'

        user_info = cursor.execute(query).fetchone()

        db.commit()

    bot_message = await bot.send_message(message.chat.id, f'<b>Имя: {user_info[0]}\n'
                                            f'Баланс:\n'
                                            f'  ▪️{round(user_info[1], 4)} RUB\n'
                                            f'  ▪️{round(user_info[2], 4)} USD\n'
                                            f'  ▪️{round(user_info[3], 4)} EUR</b>')

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


# перевод денег другому пользователю


@disp.message_handler(text='Перевести деньги другому пользователю', state=None)
async def transfer_money(message, state):
    async with state.proxy() as data_storage:
        data_storage['amount_of_tries'] = 3

    bot_message = await bot.send_message(message.chat.id, '<b>Введите пароль: </b>', reply_markup=cancel_ikb)

    await TransferStatesGroup.await_password.set()

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=TransferStatesGroup.await_password)
async def checking_password_1(message, state):
    async with state.proxy() as data_storage:
        amount_of_tries = data_storage['amount_of_tries']

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT password FROM users WHERE user_id = "{message.from_user.id}"'

        user_password = cursor.execute(query).fetchone()[0]

        db.commit()


    if message.text == user_password:
        bot_message = await bot.send_message(message.chat.id, '<b>Пароль подтвержден. Теперь отправьте никнейм человека, которому хотите перевести деньги</b>', reply_markup=cancel_ikb)

        await TransferStatesGroup.next()

        await message.delete()

    else:
        amount_of_tries -= 1

        if amount_of_tries == 0:
            bot_message = await bot.send_message(message.chat.id, '<b>У вас закончились попытки. Повторите ввод пароля через 5 минут</b>', reply_markup=cancel_ikb)

            await message.delete()

            await BlockUserState.block_user.set()

            await asyncio.sleep(7)
            await bot_message.delete()

            await asyncio.sleep(300)

            await state.finish()

            bot_message = await bot.send_message(message.chat.id, '<b>Время блокировки прошло. Теперь вы можете начать процедуру перевода средств заново(нажмите на соответствующую кнопку меню)</b>', reply_markup=cancel_ikb)

        else:
            async with state.proxy() as data_storage:
                data_storage['amount_of_tries'] = amount_of_tries

            bot_message = await bot.send_message(message.chat.id, f'<b>Введенный пароль неверен, у вас {amount_of_tries} попыток(тки)</b>', reply_markup=cancel_ikb)

            await message.delete()


    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=TransferStatesGroup.await_recipient)
async def handle_recipient(message, state):
    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        recipient_query = f'SELECT nickname, user_id FROM users WHERE nickname = "{message.text}"'
        author_nick_query = f'SELECT nickname FROM users WHERE user_id = "{message.from_user.id}"'

        recipient = cursor.execute(recipient_query).fetchone()
        recipient_nickname = recipient[0]
        recipient_user_id = recipient[1]

        author_nickname = cursor.execute(author_nick_query).fetchone()[0]

        db.commit()


    if recipient_nickname and recipient_nickname != author_nickname:
        async with state.proxy() as data_storage:
            data_storage['recipient_nick'] = recipient_nickname
            data_storage['recipient_id'] = int(recipient_user_id)
            data_storage['author_nick'] = author_nickname

        bot_message = await bot.send_message(message.chat.id, '<b>Отлично, теперь пришлите сумму, которую хотите перевести, и код валюты (RUB, USD или EUR). Например, "5.127 RUB"\nВажно:\n    ▪️вводите код валюты латиницей(регистр не так важен),\n    ▪️Сумма перевода не должна превышать 999.999 единиц валюты,\n   ▪️Разделяйте целую и дробную части точкой,\n   ▪️Дробная часть не должна превышать 4 символа.</b>', reply_markup=cancel_ikb)

        await TransferStatesGroup.next()

    else:
        bot_message = await bot.send_message(message.chat.id, '<b>Пожалуйста, введите корректное имя получателя</b>', reply_markup=cancel_ikb)


    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=TransferStatesGroup.await_amount)
async def handle_amount(message, state):
    message_data = message.text.strip().split(' ')

    amount_of_money = round(float(message_data[0]), 4)

    currency_code = message_data[1].upper()

    if currency_code in ['RUB', 'USD', 'EUR'] and amount_of_money > 0:
        if has_required_money(message, currency_code, amount_of_money):
            async with state.proxy() as data_storage:
                data_storage['amount'] = amount_of_money
                data_storage['currency_code'] = currency_code

            bot_message = await bot.send_message(message.chat.id, '<b>Хорошо, теперь пришлите комментарий к переводу</b>', reply_markup=cancel_ikb)

            await TransferStatesGroup.next()

        else:
            bot_message = await bot.send_message(message.chat.id, '<b>На вашем балансе недостаточно средств !</b>', reply_markup=cancel_ikb)

    else:
        bot_message = await bot.send_message(message.chat.id, '<b>Введен неверный код валюты(коды валют: RUB, USD, EUR) и/или неверная сумма перевода</b>', reply_markup=cancel_ikb)

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=TransferStatesGroup.await_comment)
async def handle_comment(message, state):
    async with state.proxy() as data_storage:
        data_storage['comment'] = message.text

    bot_message = await bot.send_message(message.chat.id, '<b>Теперь подвтердите выполнение операции</b>', reply_markup=accept_action_ikb)

    await TransferStatesGroup.next()

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.callback_query_handler(text='accept', state=TransferStatesGroup.await_confirmation)
async def confirm_transaction(callback, state):
    async with state.proxy() as data_storage:
       recipient_nick = data_storage['recipient_nick']
       recipient_user_id = data_storage['recipient_id']
       author_nick = data_storage['author_nick']
       amount_of_money = data_storage['amount']
       currency_code = data_storage['currency_code']
       transaction_comment = data_storage['comment']

       try:
           with sq.connect('users_accounts.db') as db:
               cursor = db.cursor()

               get_recipient_score_query = f'SELECT {currency_code} FROM users WHERE nickname = "{recipient_nick}"'
               get_author_score_query = f'SELECT {currency_code} FROM users WHERE nickname = "{author_nick}"'

               recipient_score = cursor.execute(get_recipient_score_query).fetchone()[0]
               author_score = cursor.execute(get_author_score_query).fetchone()[0]

               new_recipient_score = recipient_score + amount_of_money
               new_author_score = author_score - amount_of_money

               change_recipient_score_query = f'UPDATE users SET {currency_code} = {new_recipient_score} WHERE nickname = "{recipient_nick}"'
               change_author_score_query = f'UPDATE users SET {currency_code} = {new_author_score} WHERE nickname = "{author_nick}"'

               cursor.execute(change_recipient_score_query)
               cursor.execute(change_author_score_query)

               db.commit()


       except Exception:
           bot_message = await bot.send_message(callback.message.chat.id, '<b>Что-то пошло не так, операция отменена</b>')

           with sq.connect('users_accounts.db') as db:
               cursor = db.cursor()

               return_recipient_score_query = f'UPDATE users SET {currency_code} = {recipient_score} WHERE nickname = "{recipient_nick}"'
               return_author_score_query = f'UPDATE users SET {currency_code} = {author_score} WHERE nickname = "{author_nick}"'

               cursor.execute(return_author_score_query)
               cursor.execute(return_recipient_score_query)

               db.commit()


       else:
           bot_message = await bot.send_message(callback.message.chat.id, f'<b>Транзакция прошла успешно, вы перевели пользователю {recipient_nick}  {amount_of_money} {currency_code}.\nКомментарий:\n{transaction_comment}</b>')

           recipient_bot_message = await bot.send_message(recipient_user_id, f'<b>Вам поступил новый платеж от {author_nick} на сумму {amount_of_money} {currency_code}.\nКомментарий:\n{transaction_comment}</b>')

           await asyncio.sleep(7)
           await recipient_bot_message.delete()


       finally:
           await state.finish()

           await asyncio.sleep(7)
           await bot_message.delete()


# обмен валют


@disp.message_handler(text='Обменять валюту', state=None)
async def changing_money(message, state):
    async with state.proxy() as data_storage:
        data_storage['amount_of_tries'] = 3

    bot_message = await bot.send_message(message.chat.id, '<b>Введите пароль: </b>', reply_markup=cancel_ikb)

    await ChangingMoneyStatesGroup.await_password.set()

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=ChangingMoneyStatesGroup.await_password)
async def checking_password_2(message, state):
    async with state.proxy() as data_storage:
        amount_of_tries = data_storage['amount_of_tries']

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT password FROM users WHERE user_id = "{message.from_user.id}"'

        user_password = cursor.execute(query).fetchone()[0]

        db.commit()


    if message.text == user_password:
        await bot.send_message(message.chat.id, '<b>Пароль подтвержден. Теперь выберите тариф, по которому будете обменивать деньги</b>', reply_markup=changing_money_ikb)

        await ChangingMoneyStatesGroup.next()

        await message.delete()

    else:
        amount_of_tries -= 1

        if amount_of_tries == 0:
            bot_message = await bot.send_message(message.chat.id, '<b>У вас закончились попытки. Повторите ввод пароля через 5 минут</b>', reply_markup=cancel_ikb)

            await message.delete()

            await BlockUserState.block_user.set()

            await asyncio.sleep(7)
            await bot_message.delete()

            await asyncio.sleep(300)

            await state.finish()

            bot_message = await bot.send_message(message.chat.id, '<b>Время блокировки прошло. Теперь вы можете начать процедуру перевода средств заново(нажмите на соответствующую кнопку меню)</b>', reply_markup=cancel_ikb)

            await asyncio.sleep(7)
            await bot_message.delete()

        else:
            async with state.proxy() as data_storage:
                data_storage['amount_of_tries'] = amount_of_tries

            bot_message = await bot.send_message(message.chat.id, f'<b>Введенный пароль неверен, у вас {amount_of_tries} попыток(тки)</b>', reply_markup=cancel_ikb)

            await message.delete()

            await asyncio.sleep(7)
            await bot_message.delete()


@disp.callback_query_handler(lambda callback: callback.data in ['RUB_USD', 'USD_RUB', 'RUB_EUR', 'EUR_RUB', 'USD_EUR', 'EUR_USD'], state=ChangingMoneyStatesGroup.await_exchange_option)
async def handle_exchange_option(callback, state):
    async with state.proxy() as data_storage:
        data_storage['exchange_currency'] = callback.data[:3]
        data_storage['received_currency'] = callback.data[4:]

    bot_message = await bot.send_message(callback.message.chat.id, '<b>Отлично, теперь введите сумму, которую хотите обменять(дробную часть отделяйте точкой)</b>', reply_markup=cancel_ikb)

    await ChangingMoneyStatesGroup.next()

    await callback.message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=ChangingMoneyStatesGroup.await_amount)
async def handle_amount_of_currency(message, state):
    async with state.proxy() as data_storage:
        currency_code = data_storage['exchange_currency']

    try:
        amount_of_money = round(float(message.text), 1)

        if amount_of_money <= 0 or not has_required_money(message, currency_code, amount_of_money):
            raise RuntimeError

    except Exception:
        bot_message = await bot.send_message(message.chat.id, '<b>Введено неверное значение суммы обмена, попробуйте ввести его еще раз.</b>', reply_markup=cancel_ikb)

        await asyncio.sleep(7)
        await bot_message.delete()

    else:
        async with state.proxy() as data_storage:
            data_storage['amount_of_money'] = amount_of_money

        bot_message = await bot.send_message(message.chat.id, '<b>Отлично, теперь подтвердите выполнение операции</b>', reply_markup=accept_action_ikb)

        await ChangingMoneyStatesGroup.next()

        await asyncio.sleep(7)
        await bot_message.delete()

    finally:
        await message.delete()


@disp.callback_query_handler(text='accept', state=ChangingMoneyStatesGroup.await_confirmation)
async def handle_changing_confirmation(callback, state):

    exchange_courses = {'USD_RUB': exchange_rates.currency_courses_data.dollar_to_rub_course,
                        'RUB_USD': exchange_rates.currency_courses_data.rub_to_dollar_course,
                        'EUR_RUB': exchange_rates.currency_courses_data.eur_to_rub_course,
                        'RUB_EUR': exchange_rates.currency_courses_data.rub_to_eur_course,
                        'USD_EUR': exchange_rates.currency_courses_data.dollar_to_eur_course,
                        'EUR_USD': exchange_rates.currency_courses_data.eur_to_dollar_course}

    try:
        async with state.proxy() as data_storage:
            exchange_currency_code = data_storage['exchange_currency']
            received_currency_code = data_storage['received_currency']
            amount_of_money = data_storage['amount_of_money']
            exchange_member_id = callback.from_user.id

        with sq.connect('users_accounts.db') as db:
            cursor = db.cursor()

            currencies_query = f'SELECT {exchange_currency_code}, {received_currency_code} FROM users WHERE user_id = "{exchange_member_id}"'

            currencies = cursor.execute(currencies_query).fetchone()

            new_exchange_currency_val = currencies[0] - amount_of_money

            needed_exchange_course = exchange_courses[exchange_currency_code + '_' + received_currency_code]

            received_currency = round(needed_exchange_course * amount_of_money, 1)

            new_received_currency_val = currencies[1] + received_currency

            upload_to_db_query = f'UPDATE users SET {exchange_currency_code} = {new_exchange_currency_val}, {received_currency_code} = {new_received_currency_val} WHERE user_id = "{exchange_member_id}"'

            cursor.execute(upload_to_db_query)

            db.commit()

    except Exception:
        bot_message = await bot.send_message(callback.message.chat.id, '<b>Что-то пошло не так, операция отменена</b>')

        with sq.connect('users_accounts.db') as db:
            cursor = db.cursor()

            return_exchange_val_query = f'UPDATE users SET {exchange_currency_code} = {currencies[0]} WHERE user_id = "{exchange_member_id}"'
            return_received_val_query = f'UPDATE users SET {received_currency_code} = {currencies[1]} WHERE user_id = "{exchange_member_id}"'

            cursor.execute(return_exchange_val_query)
            cursor.execute(return_received_val_query)

            db.commit()

        await asyncio.sleep(7)
        await bot_message.delete()

    else:
        bot_message = await bot.send_message(callback.message.chat.id, f'<b>Операция была проведена успешно! На ваш счет зачислено {received_currency} {received_currency_code}</b>')

        await asyncio.sleep(7)
        await bot_message.delete()

    finally:
        await state.finish()


# пополнение баланса


@disp.message_handler(text='Пополнить баланс', state=None)
async def replenish_balance(message, state):
    async with state.proxy() as data_storage:
        data_storage['amount_of_tries'] = 3

    bot_message = await bot.send_message(message.chat.id, '<b>Введите пароль: </b>', reply_markup=cancel_ikb)

    await ReplenishTheBalanceStatesGroup.await_password.set()

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=ReplenishTheBalanceStatesGroup.await_password)
async def checking_password_3(message, state):
    async with state.proxy() as data_storage:
        amount_of_tries = data_storage['amount_of_tries']

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT password FROM users WHERE user_id = "{message.from_user.id}"'

        user_password = cursor.execute(query).fetchone()[0]

        db.commit()


    if message.text == user_password:
        bot_message = await bot.send_message(message.chat.id, '<b>Пароль подтвержден. Теперь введите сумму пополнения в рублях(дробную часть отделяйте точкой)</b>', reply_markup=cancel_ikb)

        await ReplenishTheBalanceStatesGroup.next()

        await message.delete()

        await asyncio.sleep(7)
        await bot_message.delete()

    else:
        amount_of_tries -= 1

        if amount_of_tries == 0:
            bot_message = await bot.send_message(message.chat.id, '<b>У вас закончились попытки. Повторите ввод пароля через 5 минут</b>', reply_markup=cancel_ikb)

            await message.delete()

            await BlockUserState.block_user.set()

            await asyncio.sleep(7)
            await bot_message.delete()

            await asyncio.sleep(300)

            await state.finish()

            bot_message = await bot.send_message(message.chat.id, '<b>Время блокировки прошло. Теперь вы можете начать процедуру пополнения баланса заново(нажмите на соответствующую кнопку меню).</b>', reply_markup=cancel_ikb)

            await asyncio.sleep(7)
            await bot_message.delete()

        else:
            async with state.proxy() as data_storage:
                data_storage['amount_of_tries'] = amount_of_tries

            bot_message = await bot.send_message(message.chat.id, f'<b>Введенный пароль неверен, у вас {amount_of_tries} попыток(тки)</b>', reply_markup=cancel_ikb)

            await message.delete()

            await asyncio.sleep(7)
            await bot_message.delete()


@disp.message_handler(content_types=['text'], state=ReplenishTheBalanceStatesGroup.await_amount)
async def handle_replenishment_amount(message, state):
    try:
        amount_of_money = round(float(message.text), 1)

        if amount_of_money <= 0:
            raise RuntimeError

    except Exception:
        bot_message = await bot.send_message(message.chat.id, '<b>Введено неверное значение суммы пополнения, попробуйте ввести его еще раз.</b>', reply_markup=cancel_ikb)

        await asyncio.sleep(7)
        await bot_message.delete()

    else:
        async with state.proxy() as data_storage:
            data_storage['amount_of_money'] = amount_of_money

        await bot.send_message(message.chat.id, '<b>Отлично, теперь подтвердите выполнение операции</b>', reply_markup=accept_action_ikb)

        await ReplenishTheBalanceStatesGroup.next()

    finally:
        await message.delete()


@disp.callback_query_handler(text='accept', state=ReplenishTheBalanceStatesGroup.await_confirmation)
async def confirm_replenishment(callback, state):
    amount_of_requests = 0

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT nickname FROM users WHERE user_id = "{callback.from_user.id}"'

        user_nickname = cursor.execute(query).fetchone()[0]

        db.commit()

    try:
        async with state.proxy() as data_storage:
            amount_of_money = data_storage['amount_of_money']

        replenishment_payment = Payment.create({
            'amount': {'value': str(amount_of_money), 'currency': 'RUB'},
            'description': f'Пополнение баланса аккаунта {user_nickname} на сумму {amount_of_money} RUB',
            'confirmation': {'type': 'redirect', 'return_url': 'https://web.telegram.org/z/#6221845943'}
        })

        confirm_url = replenishment_payment.confirmation.confirmation_url
        payment_id = replenishment_payment.id

        webbrowser.open_new(confirm_url)

        replenishment_scheduler = AsyncIOScheduler()

        async def capture_payment():
            nonlocal amount_of_requests

            amount_of_requests += 1

            current_payment = Payment.find_one(payment_id)

            if current_payment.status == 'waiting_for_capture':
                response = Payment.capture(payment_id, {
                    'amount': {'value': replenishment_payment.amount.value,
                               'currency': replenishment_payment.amount.currency}
                })

                if response.status == 'succeeded':
                    with sq.connect('users_accounts.db') as db:
                        cursor = db.cursor()

                        query = f'UPDATE users SET RUB = RUB + {amount_of_money} WHERE user_id = "{callback.from_user.id}"'

                        cursor.execute(query)

                        db.commit()

                    bot_message = await bot.send_message(callback.message.chat.id, '<b>Ваш баланс был успешно пополнен</b>')

                    await asyncio.sleep(7)
                    await bot_message.delete()

                    replenishment_scheduler.shutdown()

                else:
                    replenishment_scheduler.shutdown()

                    raise RuntimeError


            if amount_of_requests >= 55:
                _ = Payment.cancel(payment_id)

                replenishment_scheduler.shutdown()

                raise RuntimeError


        replenishment_scheduler.add_job(capture_payment, 'interval', seconds=5)

        replenishment_scheduler.start()


    except Exception:
        bot_message = await bot.send_message(callback.message.chat.id, '<b>Что-то не так, платеж был отменен</b>')

        await asyncio.sleep(7)
        await bot_message.delete()


    finally:
        await state.finish()

        await callback.message.delete()


# выплаты


@disp.message_handler(text='Вывести деньги', state=None)
async def withdraw_money(message, state):
    async with state.proxy() as data_storage:
        data_storage['amount_of_tries'] = 3

    bot_message = await bot.send_message(message.chat.id, '<b>Введите пароль: </b>', reply_markup=cancel_ikb)

    await WithdrawMoneyStatesGroup.await_password.set()

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


@disp.message_handler(content_types=['text'], state=WithdrawMoneyStatesGroup.await_password)
async def checking_password_4(message, state):
    async with state.proxy() as data_storage:
        amount_of_tries = data_storage['amount_of_tries']

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT password FROM users WHERE user_id = "{message.from_user.id}"'

        user_password = cursor.execute(query).fetchone()[0]

        db.commit()


    if message.text == user_password:
        bot_message = await bot.send_message(message.chat.id, '<b>Пароль подтвержден. Теперь введите сумму выплаты выплаты в рублях(дробную часть отделяйте точкой)</b>', reply_markup=cancel_ikb)

        await WithdrawMoneyStatesGroup.next()

        await message.delete()

        await asyncio.sleep(7)
        await bot_message.delete()

    else:
        amount_of_tries -= 1

        if amount_of_tries == 0:
            bot_message = await bot.send_message(message.chat.id, '<b>У вас закончились попытки. Повторите ввод пароля через 5 минут</b>', reply_markup=cancel_ikb)

            await message.delete()

            await BlockUserState.block_user.set()

            await asyncio.sleep(7)
            await bot_message.delete()

            await asyncio.sleep(300)

            await state.finish()

            bot_message = await bot.send_message(message.chat.id, '<b>Время блокировки прошло. Теперь вы можете начать процедуру вывода средств заново(нажмите на соответствующую кнопку меню).</b>', reply_markup=cancel_ikb)

            await asyncio.sleep(7)
            await bot_message.delete()

        else:
            async with state.proxy() as data_storage:
                data_storage['amount_of_tries'] = amount_of_tries

            bot_message = await bot.send_message(message.chat.id, f'<b>Введенный пароль неверен, у вас {amount_of_tries} попыток(тки)</b>', reply_markup=cancel_ikb)

            await message.delete()

            await asyncio.sleep(7)
            await bot_message.delete()


@disp.message_handler(content_types=['text'], state=WithdrawMoneyStatesGroup.await_amount)
async def handle_withdrawal_amount(message, state):
    try:
        amount_of_money = f'{round(float(message.text), 2):.2f}'

        if float(amount_of_money) <= 0 or not has_required_money(message, 'RUB', float(amount_of_money)):
            raise RuntimeError

    except Exception:
        bot_message = await bot.send_message(message.chat.id, '<b>Введено неверное значение суммы вывода, попробуйте ввести его еще раз.</b>', reply_markup=cancel_ikb)

        await asyncio.sleep(7)
        await bot_message.delete()

    else:
        async with state.proxy() as data_storage:
            data_storage['amount_of_money'] = amount_of_money

        await bot.send_message(message.chat.id, '<b>Отлично, теперь подтвердите выполнение операции</b>', reply_markup=accept_action_ikb)

        await WithdrawMoneyStatesGroup.next()

    finally:
        await message.delete()


@disp.callback_query_handler(text='accept', state=WithdrawMoneyStatesGroup.await_confirmation)
async def confirm_withdrawal(callback, state):
    amount_of_requests = 0

    async with state.proxy() as data_storage:
        amount_of_money = data_storage['amount_of_money']

    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT nickname FROM users WHERE user_id = "{callback.from_user.id}"'

        user_nickname = cursor.execute(query).fetchone()[0]

        db.commit()

    bot_message = await bot.send_message(callback.message.chat.id, '<b>Через несколько секунд появится поле, в котором вы должны ввести данные для совершения выплаты. Обратите внимание, это тестовая оплата, нужная для получения ваших платежных реквизитов. Деньги со счета списаны не будут.</b>')

    try:
        replenishment_payment = Payment.create({
            'amount': {'value': '1', 'currency': 'RUB'},
            'confirmation': {'type': 'redirect', 'return_url': 'https://web.telegram.org/z/#6221845943'},
            'save_payment_method': True
        })

        confirm_url = replenishment_payment.confirmation.confirmation_url
        payment_id = replenishment_payment.id

        await asyncio.sleep(7)

        await bot_message.delete()

        webbrowser.open_new(confirm_url)

        get_payment_id_scheduler = AsyncIOScheduler()

        async def get_payment_method_id():
            nonlocal amount_of_requests

            amount_of_requests += 1

            current_payment = Payment.find_one(payment_id)

            if current_payment.status == 'waiting_for_capture':
                payment_method_id = current_payment.payment_method.id

                _ = Payment.cancel(payment_id)

                headers = {
                    'Idempotence-Key': str(uuid.uuid4()),
                    'Content-Type': 'application/json',
                }

                json_data = {
                    'amount': {'value': str(amount_of_money), 'currency': 'RUB'},
                    'payment_method_id': payment_method_id,
                    'description': f'выплата в размере {amount_of_money} RUB пользователю {user_nickname}'
                }

                url = 'https://api.yookassa.ru/v3/payouts'

                response = post(url, headers=headers, json=json_data, auth=(payout_account_id, payout_secret_key))

                if response.json()['status'] == 'succeeded':
                    with sq.connect('users_accounts.db') as db:
                        cursor = db.cursor()

                        query = f'UPDATE users SET RUB = RUB - {amount_of_money} WHERE user_id = "{callback.from_user.id}"'

                        cursor.execute(query)

                        db.commit()

                    bot_message = await bot.send_message(callback.message.chat.id, '<b>Выплата на ваш счет была успешно совершена! </b>')

                    await asyncio.sleep(7)
                    await bot_message.delete()

                    get_payment_id_scheduler.shutdown()

                else:
                    get_payment_id_scheduler.shutdown()

                    raise RuntimeError

            if amount_of_requests >= 55:
                _ = Payment.cancel(payment_id)

                get_payment_id_scheduler.shutdown()

                raise RuntimeError


        get_payment_id_scheduler.add_job(get_payment_method_id, 'interval', seconds=5)

        get_payment_id_scheduler.start()


    except Exception:
        bot_message = await bot.send_message(callback.message.chat.id, '<b>Что-то не так, выплата была отменена</b>')

        await asyncio.sleep(7)
        await bot_message.delete()


    finally:
        await state.finish()

        await callback.message.delete()

# служба поддержки

@disp.message_handler(text='Служба поддержки', state=None)
async def connect_support_service(message):
    bot_message = await bot.send_message(message.chat.id, '<b>Если у вас появились какие-то вопросы, связанные с работой бота, можете обратиться в службу поддержки по следующему контакту: https://t.me/ThisIsMyShadow</b>')

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


# условия пользования

@disp.message_handler(text='Условия пользования', state=None)
async def show_terms(message):
    bot_message = await bot.send_message(message.chat.id, '<b>Условия пользования ботом:\n'
                                                          '▪️Бот является некоммерческим проектом, все операции производятся без участия реальных денежных средств.\n'
                                                          '▪️Бот не собирает о вас никакой конфиденциальной информации, кроме вашего пароля. Все данные банковских счетов защищены по мировому стандарту PCI DSS.\n'
                                                          '▪️Бот создан с целью развлечения и не преследует никаких других целей.\n'
                                                          '▪️Для работы с ботом вы можете использовать данные тестовой карты: 5555 5555 5555 4477 или любой другой из этой статьи https://yookassa.ru/developers/payment-acceptance/testing-and-going-live/testing (все данные номера тестовых карт поддерживаются эквайрингом Юкасса). Дата действия карты может быть любой, большей текущей даты. CVC код и 3-D SECURE могут быть любыми допустимыми(формат: только цифры).\n'
                                                          '▪️Если у вас появились какие-то вопросы или предложения, свяжитесь со службой поддержки через соответствующую вкладку меню.</b>')

    await message.delete()

    await asyncio.sleep(7)
    await bot_message.delete()


if __name__ == '__main__':
    exchange_rates.scheduler.start()
    executor.start_polling(disp, skip_updates=True, on_startup=on_startup)
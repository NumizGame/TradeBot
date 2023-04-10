from aiogram.types import *

start_registration_ikb = InlineKeyboardMarkup()
start_reg_btn = InlineKeyboardButton('Начать регистрацию', callback_data='start_reg')

start_registration_ikb.add(start_reg_btn)

main_menu_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
check_course_btn = KeyboardButton('Посмотреть курсы валют')
show_profile_btn = KeyboardButton('Показать профиль')
replenish_balance_btn = KeyboardButton('Пополнить баланс')
withdraw_money_btn = KeyboardButton('Вывести деньги')
transfer_money_btn = KeyboardButton('Перевести деньги другому пользователю')
change_money_btn = KeyboardButton('Обменять валюту')
contact_support_btn = KeyboardButton('Служба поддержки')
terms_of_use_btn = KeyboardButton('Условия пользования')

main_menu_kb.add(check_course_btn, show_profile_btn, replenish_balance_btn, withdraw_money_btn, transfer_money_btn, change_money_btn, contact_support_btn, terms_of_use_btn)

accept_action_ikb = InlineKeyboardMarkup()
accepting_btn = InlineKeyboardButton('✅', callback_data='accept')
cancelling_btn = InlineKeyboardButton('❌', callback_data='cancel')
accept_action_ikb.add(accepting_btn, cancelling_btn)

cancel_ikb = InlineKeyboardMarkup()
cancel_ikb.add(cancelling_btn)

changing_money_ikb = InlineKeyboardMarkup(row_width=2)
exchange_rub_for_usd = InlineKeyboardButton('RUB -> USD', callback_data='RUB_USD')
exchange_usd_for_rub = InlineKeyboardButton('USD -> RUB', callback_data='USD_RUB')

exchange_rub_for_eur = InlineKeyboardButton('RUB -> EUR', callback_data='RUB_EUR')
exchange_eur_for_rub = InlineKeyboardButton('EUR -> RUB', callback_data='EUR_RUB')

exchange_usd_for_eur = InlineKeyboardButton('USD -> EUR', callback_data='USD_EUR')
exchange_eur_for_usd = InlineKeyboardButton('EUR -> USD', callback_data='EUR_USD')

changing_money_ikb.add(exchange_rub_for_usd, exchange_usd_for_rub, exchange_rub_for_eur, exchange_eur_for_rub, exchange_eur_for_usd, exchange_usd_for_eur, cancelling_btn)
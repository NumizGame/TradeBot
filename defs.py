import sqlite3 as sq

async def entering_into_the_database(state):
    try:
        async with state.proxy() as data_storage:
            user_nickname = data_storage['nickname']
            user_password = data_storage['password']
            user_id = data_storage['user_id']

        with sq.connect('users_accounts.db') as db:
            cursor = db.cursor()

            query = f'''INSERT INTO users VALUES ('{user_id}', '{user_nickname}', '{user_password}', 0, 0, 0)'''

            cursor.execute(query)

            db.commit()

    except Exception:
        return False

    else:
        return True


def is_registered(user_id):
    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT nickname FROM users WHERE user_id = "{user_id}"'

        user_nickname = cursor.execute(query).fetchone()

        db.commit()

    if user_nickname:
        return True

    return False


def has_required_money(message, currency_code, amount_of_money):
    with sq.connect('users_accounts.db') as db:
        cursor = db.cursor()

        query = f'SELECT {currency_code} FROM users WHERE user_id = "{message.from_user.id}"'

        user_balance = cursor.execute(query).fetchone()[0]

        db.commit()

    if user_balance >= amount_of_money:
        return True

    else:
        return False
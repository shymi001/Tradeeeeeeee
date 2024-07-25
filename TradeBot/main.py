from aiogram import Bot, Dispatcher, executor, types
import aiohttp
from aiogram import types
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import random
import datetime
import asyncio
import requests
import mysql
import mysql.connector
from mysql.connector import Error, pooling

from config import TOKEN, TWO_TOKEN, CHAT_USER_ID, altcoins
from config import db_data, db_host, db_pass, db_port, db_user, connection

last_api_request_time = 0
logging.basicConfig(level=logging.INFO)
NOTIFICATION_BOT_TOKEN = TWO_TOKEN  #второй бот
NOTIFICATION_BOT_CHAT_ID = CHAT_USER_ID #кому отправлять сообщение
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
notification_dp = Bot(token=NOTIFICATION_BOT_TOKEN)
notification_dp = Dispatcher(notification_dp)
print(altcoins)
user_balances = {}
file_id = "CAACAgUAAxkBAAKfKWZTIiBxjIH4ufOA8WdYjZws7RuPAAJrAwACAmDwV2FMLc7Ps_79NQQ"
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="123",
            database="user_id_telegram"
        )
        print("[OK] База данных подключена")
    except Error as e:
        print(f"[error] '{e}'")
    return connection

#Проверка базы данных
def create_table(connection, table_name, create_table_query):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
        result = cursor.fetchone()
        if result:
            print(f"[OK] Таблица '{table_name}' уже существует")
        else:
            cursor.execute(create_table_query)
            connection.commit()
            print(f"[OK] Таблица '{table_name}' успешно создана")
    except Error as e:
        print(f"[error] '{e}'")




timer_active = False
top_up_amount = 0
top_up_user_id = None

class BuyState(StatesGroup):
    amount = State()

class TopUpState(StatesGroup):
    amount = State()

class PageState(StatesGroup):
    page = State()

class InvestState(StatesGroup):
    waiting_for_investment = State()

class InvestProcess(StatesGroup):
    waiting_for_amount = State()
    waiting_for_direction = State()

class InvestProcess(StatesGroup):
    waiting_for_amount = State()
    waiting_for_manual_amount = State()
    waiting_for_direction = State()
    waiting_for_wait_time = State()

class WithdrawProcess(StatesGroup):
    waiting_for_withdraw_amount = State()
    waiting_for_card_details = State()

class SellState(StatesGroup):
    amount = State()

class SellStates(StatesGroup):
    waiting_for_quantity = State()
    confirm_sell = State()

crypto_display_names = {
    'bitcoin': 'Bitcoin/USD',
    'ethereum': 'Ethereum/USD',
    'qtum': 'Qtum/USD',
    'tron': 'Tron/USD',
    'litecoin': 'Litecoin/USD',
    'ripple': 'Ripple/USD',
    'cardano': 'Cardano/USD',
    'solana': 'Solana/USD',
    'dogecoin': 'Dogecoin/USD',
    'polkadot': 'Polkadot/USD',
    'maker': 'Maker/USD',
    'quant': 'Quant/USD',
    'busd': 'BUSD/USD',
    'optimism': 'Optimism/USD',
    'okb': 'OKB/USD',
    'shiba': 'Shiba Inu/USD',
    'apecoin': 'ApeCoin/USD',
    'dai': 'Dai/USD',
    'stellar': 'Stellar/USD',
    'stepn': 'STEPN/USD',
    'wreppedbitcoin': 'Wrapped Bitcoin/USD',
    'near': 'Near/USD',
    'gala': 'Gala/USD',
    'cronos': 'Cronos/USD'
}

top_up_user_id = None
selected_crypto = None
crypto_wallets = {
    'tron': 'TRON_WALLET_ADDRESS',
    'toncoin': 'UQAR-uQI8owPa_IIsbpTgy6E97HHriUJoEqKH-vxPkkCnjqU',
    'eth': 'ETH_WALLET_ADDRESS',
    'usdt': 'TTvMYqS6EcQr6ugcJoP5s6B5iARx2HdMuR',
    'notcoin': 'UQAR-uQI8owPa_IIsbpTgy6E97HHriUJoEqKH-vxPkkCnjqU'
}

def is_in_top_up_process(user_id):
    global top_up_user_id
    return top_up_user_id == user_id

async def get_crypto_price(crypto, currency):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies={currency}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logging.info(f"API response: {data}")
                    
                    # Добавим вывод данных о цене криптовалюты
                    logging.info(f"Price data for {crypto} in {currency}: {data.get(crypto)}")
                    
                    price = data.get(crypto, {}).get(currency)
                    if price is None:
                        logging.error(f"Price for {crypto} in {currency} is not found in the response")
                        return None
                    return price
                else:
                    logging.error(f"Error fetching crypto price: {response.status} {response.reason}")
                    return None
    except Exception as e:
        logging.error(f"Exception fetching crypto price: {e}")
        return None

try:
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        database=db_data,
        port=db_port
    )

    if connection.is_connected():
        print("Connected to MySQL database")

except mysql.connector.Error as err:
    print(f"ОШИБКА ДАЛБАЕБ: {err}")


finally:
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection is closed")

async def send_my_cabinet(message: types.Message):
    # Генерация случайного числа в диапазоне от 1100 до 1200
    online_count = random.randint(1100, 1200)
    
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0)
    # Генерация случайного цвета для Bitcoin и Ethereum
    bitcoin_load = get_random_load_color()
    ethereum_load = get_random_load_color()
    
    # Извлекаем монету и её цвет из списка альтернативных монет
    altcoin = altcoins.pop(0)
    altcoin_load = altcoin["name:"] + ": " + altcoin["color"]
    # Помещаем извлеченную монету в конец списка, чтобы она стала последней при следующем вызове
    altcoins.append(altcoin)

    # Создаем инлайн клавиатуру
    keyboard = InlineKeyboardMarkup(row_width=2)  # Устанавливаем количество кнопок в строке (в данном случае - 2)
    # Добавляем кнопки
    keyboard.add(
        InlineKeyboardButton("💳Пополнить", callback_data='top_up'),
        InlineKeyboardButton("💰Вывод средств", callback_data='withdraw'),
        InlineKeyboardButton("🛡️Верификация", callback_data='verification'),
        InlineKeyboardButton("⚙️Настройки", callback_data='settings')
    )
        
    my_cabinet_message = f"""
🔐 Личный кабинет
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
🛡️ Верификация: ❌
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
🏦 Общий баланс: {balance} ₽
🆔 ID: {user_id}
📊 Всего сделок: 0
✅ Удачных: 0
❌ Неудачных: 0
💰 Выводов совершено 0 на сумму 0 ₽
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
👥 Пользователей онлайн: {online_count}

Загруженность Bitcoin: {bitcoin_load}
Загруженность Ethereum: {ethereum_load}
Загруженность {altcoin_load}
"""
    
    photo_url = 'https://ibb.co/8dxBz4M'  # Замени URL на прямую ссылку на изображение
    
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=my_cabinet_message,
        reply_markup=keyboard  # Добавляем инлайн клавиатуру
    )

# Функция для выбора случайного цвета загруженности
def get_random_load_color():
    return random.choice(["🟡", "🟢", "🔴"])

@dp.callback_query_handler(lambda call: call.data == 'top_up')
async def process_top_up(call: types.CallbackQuery):
    top_up_keyboard = InlineKeyboardMarkup(row_width=1)
    top_up_keyboard.add(
        InlineKeyboardButton("💳Пополнить через банковскую карту", callback_data='top_up_card'),
        InlineKeyboardButton("💱Пополнить криптовалютой", callback_data='top_up_crypto')
    )
    
    await call.message.edit_caption(
        caption="Выберите вариант пополнения баланса:",
        reply_markup=top_up_keyboard
    )

@dp.callback_query_handler(lambda call: call.data == 'top_up_card')
async def process_top_up_card(call: types.CallbackQuery):
    # Отправляем текстовое сообщение
    await call.message.answer("""
<i>Просим искренние прощения.

Сейчас у нас на сервере идут технические неполадки.</i>
""", parse_mode='HTML')

    # Отправляем стикер
    await call.message.reply_sticker("CAACAgIAAxkBAAK2q2aibTThRZAMaQxi-54Cqpp4PRl8AAJ-AQACK15TC4qyw0Zen8nxNQQ")

# Обработка нажатий на кнопки
async def get_crypto_price(crypto, currency="rub"):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies={currency}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            logging.info(f"Received data from CoinGecko: {data}")
            return data[crypto][currency]

def is_in_top_up_process(user_id):
    global top_up_user_id
    return top_up_user_id == user_id

@dp.callback_query_handler(lambda call: call.data in ['top_up_crypto_tron', 'top_up_crypto_toncoin', 'top_up_crypto_eth', 'top_up_crypto_usdt', 'top_up_crypto_notcoin'])
async def process_crypto_top_up(call: types.CallbackQuery):
    global selected_crypto, top_up_user_id
    top_up_user_id = call.from_user.id
    selected_crypto = call.data.split('_')[-1]  # tron, toncoin, eth, usdt, notcoin

    await bot.send_message(call.from_user.id, "Введите сумму в рублях:")

@dp.message_handler(lambda message: message.text.isdigit() and is_in_top_up_process(message.from_user.id))
async def process_top_up_amount(message: types.Message):
    global selected_crypto
    try:
        amount_rub = float(message.text)
        crypto_ids = {
            'tron': 'tron',
            'toncoin': 'the-open-network',
            'eth': 'ethereum',
            'usdt': 'tether',
            'notcoin': 'notcoin'
        }
        crypto_id = crypto_ids[selected_crypto]
        crypto_price = await get_crypto_price(crypto_id, "rub")  # Убедитесь, что передаем оба аргумента
        amount_crypto = round(amount_rub / crypto_price, 8)

        wallet_address = crypto_wallets[selected_crypto]

        await bot.send_message(
            message.chat.id,
            f"♻️ Оплата {selected_crypto.upper()}\n\n"
            f"Сумма: {amount_crypto} {selected_crypto.upper()}\n"
            f"Реквизиты для оплаты: {wallet_address}\n\n"
            f"⚠️ Курс зафиксирован на 60 минут!\n"
            f"⚠️ Учтите комиссию вашей биржи, на наши реквизиты должна прийти ровно та сумма которая указана выше. Если по "
            f"какому-то стечению обстоятельств сумма пришла не та - напишите в техническую поддержку.\n\n"
            f"⚠️ Средства зачисляются автоматически, в ином случае присылайте квитанцию в поддержку!"
        )
        top_up_user_id = None  # Сбросить процесс пополнения
    except Exception as e:
        await message.reply("Произошла ошибка. Пожалуйста, попробуйте снова.")
        logging.error(f"Error processing top up amount: {e}")

async def send_top_up_options(call: types.CallbackQuery):
    top_up_keyboard = InlineKeyboardMarkup(row_width=1)
    top_up_keyboard.add(
        # InlineKeyboardButton("Tron (TRC20)", callback_data='top_up_crypto_tron'),
        InlineKeyboardButton("Toncoin", callback_data='top_up_crypto_toncoin'),
        InlineKeyboardButton("Ethereum (ETH)", callback_data='top_up_crypto_eth'),
        InlineKeyboardButton("Tether (USDT)", callback_data='top_up_crypto_usdt'),
        InlineKeyboardButton("Notcoin", callback_data='top_up_crypto_notcoin')
    )
    
    await call.message.edit_caption(
        caption="Выберите криптовалюту для пополнения:",
        reply_markup=top_up_keyboard
    )

@dp.callback_query_handler(lambda call: call.data == 'top_up_crypto')
async def process_top_up(call: types.CallbackQuery):
    await send_top_up_options(call)

@dp.callback_query_handler(lambda call: call.data == 'start_top_up')
async def start_top_up(call: types.CallbackQuery):
    await send_top_up_options(call)


# async def send_bank_options(call: types.CallbackQuery):
#     bank_keyboard = InlineKeyboardMarkup(row_width=1)
#     bank_keyboard.add(
#         InlineKeyboardButton("СберБанк", callback_data='sberbank'),
#         InlineKeyboardButton("Тинькофф", callback_data='tinkoff')
#     )
    
#     await call.message.edit_caption(
#         caption="Выберите банк для пополнения:",
#         reply_markup=bank_keyboard
#     )
# async def process_bank_selection(call: types.CallbackQuery, bank_name: str):
#     await call.message.answer(
#         text="Введите сумму пополнения:\n\nМинимальная сумма: 1000 рублей")

# async def start_timer(finish_time, chat_id):
#     while datetime.datetime.now() < finish_time:
#         await asyncio.sleep(60)
#     # Если время истекло, отправляем сообщение
#     await bot.send_message(chat_id, "Поздно, дружище! Время для оплаты истекло.")
#     # Сбрасываем флаг активности таймера
#     global timer_active
#     timer_active = False

# @dp.message_handler(lambda message: message.text.isdigit())
# async def process_top_up_amount(message: types.Message, state: FSMContext):
#     # data = await state.get_data()
#     global timer_active, top_up_amount
#     try:
#         number = float(message.text)    
#         if number < 1000:
#             await bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAKfK2ZTJHkIu8z1DDCKX4PfYiFsaKKSAAIPDAAC4o45Si0XN8xNQrdQNQQ')
#             await message.answer("Минимальная сумма пополнения: 1000 рублей.")
#         elif number > 40000:
#             await bot.send_sticker(message.chat.id, sticker='CAACAgIAAxkBAAKfK2ZTJHkIu8z1DDCKX4PfYiFsaKKSAAIPDAAC4o45Si0XN8xNQrdQNQQ')
#             await message.answer("Максимальная сумма пополнения: 40000 рублей.")
#         else:
#             top_up_amount = number  # Сохраняем значение суммы пополнения
#             finish_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
#             formatted_time = finish_time.strftime("%H:%M")
#             keyboard = types.InlineKeyboardMarkup(row_width=1)
#             keyboard.add(
#                 types.InlineKeyboardButton(text="✅Пополнил(а)", callback_data="confirmed"),
#                 types.InlineKeyboardButton(text="❌Отменить", callback_data="back")
#             )
#             await message.answer(
#                 text=f"♻️ Оплата банковской картой:\n\n"
#                      f"Сумма: {number} ₽\n\n"
#                      f"Реквизиты для оплаты банковской картой:\n"
#                      f"└0000-0000-0000-0000\n\n"
#                      f"Реквизиты для оплаты через СБП (МТС BANK):\n"
#                      f"└0000-0000-0000-0000\n\n"
#                      f"‼️Оплатите точную сумму указанную в строке «Сумма» по указанным реквизитам.\n"
#                      f"После оплаты баланс будет зачислен на Ваш аккаунт автоматически в течении нескольких минут.\n\n"
#                      f"У Вас осталось до {formatted_time} для оплаты",
#                 reply_markup=keyboard
#             )
#             if not timer_active:
#                 timer_active = True
#                 await start_timer(finish_time, message.chat.id)
#     except ValueError:
#         await message.answer("Введите числовое значение суммы пополнения.")
#         # await state.finish() 

# Обработчик для нажатия на кнопку "Пополнил(а)"
@dp.callback_query_handler(lambda call: call.data == 'confirmed')
async def confirm_top_up(call: types.CallbackQuery):
    global top_up_amount
    user_id = call.from_user.id
    amount = top_up_amount

    notification_message = f"К вам новый клиент @{call.from_user.username} пополняет баланс на {amount} рублей."
    notify_payload = {
        'chat_id': NOTIFICATION_BOT_CHAT_ID,
        'text': notification_message,
        'reply_markup': {
            'inline_keyboard': [
                [
                    {'text': 'Одобрить', 'callback_data': f'approve_{user_id}_{amount}'}
                ]
            ]
        }
    }
    requests.post(f'https://api.telegram.org/bot{NOTIFICATION_BOT_TOKEN}/sendMessage', json=notify_payload)

    await call.message.answer("Запрос на пополнение отправлен.")

# Обработчик для кнопки "Одобрить"
@notification_dp.callback_query_handler(lambda c: c.data.startswith('approve_'))
async def handle_approve(call: types.CallbackQuery):
    _, user_id, amount = call.data.split('_')
    user_id = int(user_id)
    amount = float(amount)
    
    # Отправка запроса на обновление баланса боту Трейдинг
    update_balance_response = requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        json={
            'chat_id': user_id,
            'text': f"Ваш баланс пополнен на {amount} рублей."
        }
    )
    
    if update_balance_response.status_code == 200:
        # Обновление локального баланса
        if user_id in user_balances:
            user_balances[user_id] += amount
        else:
            user_balances[user_id] = amount
        await call.message.answer("Баланс успешно обновлен.")
    else:
        await call.message.answer("Произошла ошибка при обновлении баланса.")

@dp.callback_query_handler(lambda call: call.data == 'confirmed')
async def start_command_start(message: types.Message):
    await process_top_up(message)   

# @dp.callback_query_handler(lambda c: c.data.startswith('approve_'))
# async def handle_approve(call: types.CallbackQuery):
#     # Извлекаем user_id и amount из callback_data
#     _, user_id, amount = call.data.split('_')
#     user_id = int(user_id)
#     amount = float(amount)
    
#     # Отправляем запрос на бот "Трейдинг" для обновления баланса
#     trade_payload = {
#         'user_id': user_id,
#         'amount': amount
#     }
#     response = requests.post(f'http://your_trading_bot_url/update_balance', json=trade_payload)
    
#     if response.status_code == 200:
#         await call.message.answer("Баланс успешно обновлен.")
#     else:
#         await call.message.answer("Произошла ошибка при обновлении баланса.")




# @dp.callback_query_handler(lambda call: call.data == 'confirmed') 
# async def confirmed_new(call: types.CallbackQuery):
#     await call.message.answer(
#         text="""
# ✅ После зачисления платежа - Ваш счёт будет автоматически пополнен!
# Если этого не произошло в течении 10 минут после оплаты, свяжитесь с Тех.Поддержкой.
# """)

@dp.callback_query_handler(lambda call: call.data == 'back') 
async def back_new(call: types.CallbackQuery):
    await send_my_cabinet(call.message)  # Перезапускаем стартовую функцию

@dp.callback_query_handler(lambda call: call.data == 'sberbank')
async def process_sberbank_selection(call: types.CallbackQuery):
    await process_bank_selection(call, "Сбербанк")

@dp.callback_query_handler(lambda call: call.data == 'tinkoff')
async def process_tinkoff_selection(call: types.CallbackQuery):
    await process_bank_selection(call, "Тинькофф")

@dp.callback_query_handler(lambda call: call.data == 'top_up_card')
async def process_top_up_card(call: types.CallbackQuery):
    await send_bank_options(call)

@dp.callback_query_handler(lambda call: call.data == 'withdraw')
async def process_withdraw(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_balance = await get_user_balance(user_id)  # Получаем баланс пользователя

    await call.message.answer(f"""💰Введите сумму вывода:
                              
У вас на балансе: {user_balance} ₽
Минимальная сумма вывода: 1000 ₽
""")
    await WithdrawProcess.waiting_for_withdraw_amount.set()

@dp.message_handler(state=WithdrawProcess.waiting_for_withdraw_amount)
async def withdraw_amount_entered(message: types.Message, state: FSMContext):
    # Если пользователь ввел команду /start, выходим из состояния и возвращаемся в главное меню
    if message.text == '/start':
        await state.finish()
        await start(message)
        return
    
    try:
        amount = int(message.text)
        user_balance = await get_user_balance(message.from_user.id)
        
        if amount < 1000:
            await message.reply("Минимальная сумма вывода: 1000 ₽. Пожалуйста, введите другую сумму или введите /start для возврата в главное меню.")
            return
        
        if user_balance < amount:
            await message.reply("На вашем балансе недостаточно средств. Пожалуйста, введите другую сумму или введите /start для возврата в главное меню.")
            return

        await state.update_data(amount=amount)
        await message.reply("💳 Введите реквизиты на которые поступит вывод средств:\n\n⚠️ Вывод средств возможен только на реквизиты, с которых пополнялся ваш баланс! ⚠️")
        await WithdrawProcess.waiting_for_card_details.set()
        
    except ValueError:
        await message.reply("Пожалуйста, введите правильную сумму или введите /start для возврата в главное меню.")

@dp.message_handler(state=WithdrawProcess.waiting_for_card_details)
async def card_details_entered(message: types.Message, state: FSMContext):
    card_number = message.text.strip()
    
    if len(card_number) != 16 or not card_number.isdigit():
        await message.reply("Некорректный формат. Введите 16 цифр номера карты.")
        return

    # Получаем сумму вывода из состояния
    data = await state.get_data()
    amount = data.get('amount')
    
    await message.reply("Ваша заявка на вывод была успешно создана.\nВывод средств может занимать время от 60 минут до 3х часов. Если деньги не поступили в течение этого времени, обратитесь в Тех.Поддержку.")
    await state.finish()

@dp.callback_query_handler(lambda call: call.data == 'verification')
async def process_verification(call: types.CallbackQuery):
    # Текст сообщения
    text = """
🤷🏻 К сожалению, ваш аккаунт не верифицирован

Рекомендуем верифицировать аккаунт, вы можете это сделать, нажав на кнопку ниже и написав 'Верификация' в тех.поддержку, спасибо!

🏆 Преимущества верифицированного кабинета:

🔷 Приоритет в очереди к выплате.
🔷 Отсутствие лимитов на вывод средств.
🔷 Возможность хранить средства на балансе бота в разных активах.
🔷 Увеличение доверия со стороны администрации, предотвращения блокировки аккаунта.
"""
    support_username = "akapovich001"
    support_link = f"https://t.me/{support_username}"
    
    # Создание клавиатуры с двумя кнопками
    support_keyboard = InlineKeyboardMarkup(row_width=1)
    support_keyboard.add(
        InlineKeyboardButton("Пройти верификацию", url=support_link),
        InlineKeyboardButton("🔙", callback_data="back")
    )

    # Отправка текста "❌"
    await bot.send_message(
        chat_id=call.message.chat.id,
        text="❌"
    )

    # Отправка основного сообщения с кнопками
    await bot.send_message(
        chat_id=call.message.chat.id,
        text=text,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=support_keyboard
    )

@dp.callback_query_handler(lambda call: call.data == 'settings')
async def process_settings(call: types.CallbackQuery):
    # Отправка текста
    await call.message.answer("""
Пока что ничего, в скором времени добавим
""")
    # Отправка стикера
    await bot.send_sticker(call.message.chat.id, sticker='CAACAgIAAxkBAAK2qWaiYOx1giG_0PqtmSTbBpQZlXpyAAJEFwACHmv5S2V-zNd5lwgcNQQ')


async def send_my_us(message: types.Message):
    my_future_message = """
TokenTrade - централизованная биржа для торговли криптовалютой и фьючерсными активами.


🔹Ведущие инновации
┗ Мы не стоим на месте и находимся в постоянном стремлении к совершенству. Внедрение передовых решений и
установление новых тенденций делает нас лидерами отрасли.


🔹Лояльность клиентов
┗ Доступная каждому возможность стать профессиональным трейдером. Установление долгосрочных отношений за счет
отзывчивости и регулярного оказания первоклассных услуг.


🔹Общий успех
┗ Наша задача — предоставлять клиентам по всему миру простую и доступную торговлю, которая позволяет зарабатывать
на финансовых рынках в любое время и в любом месте.


Благодаря простому пользовательскому интерфейсу TokenTrade прекрасно подходит для новичков.
На платформе легко ориентироваться, что привлекает как продвинутых, так и начинающих трейдеров и инвесторов.
""" 
    photo_url = 'https://ibb.co.com/5X0NCQK'  # Замени URL на прямую ссылку на изображение
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
    InlineKeyboardButton("📖Условие",url='https://telegra.ph/Individual-Contributor-License-Agreement--Nazvanie-Birzhi-02-07'),
    InlineKeyboardButton("📜 Сертификат", callback_data='sertificat')
)

# Добавляем кнопку "Гарантия сервиса" в середину и делаем ее длиннее остальных кнопок
    keyboard.insert(
    InlineKeyboardButton("🔐 Гарантия сервиса", callback_data='garant_service')
    )
    keyboard.add(
    InlineKeyboardButton("👥 Реферальная система", callback_data='ref_sistem')
)



    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=my_future_message,
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'sertificat')
async def process_callback_sertificat(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    photo_url = 'https://imgbly.com/ib/7miULaQDBP'
    await bot.send_photo(callback_query.from_user.id, photo=photo_url)

@dp.callback_query_handler(lambda c: c.data == 'garant_service')
async def process_callback_garant_service(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    chat_id = callback_query.message.chat.id
    my_text = """
🔹 TokenTrade - онлайн-биржа, предоставляющая услуги торговли бинарными опционами и другими финансовыми инструментами.

Важно понимать, что в любой финансовой сфере существуют риски, связанные с инвестированием и торговлей.
Поэтому никакая биржа или компания не может дать полные гарантии прибыли или отсутствия рисков.
Тем не менее, TokenTrade может предоставить своим клиентам некоторые гарантии, чтобы обеспечить надежность и
безопасность своих услуг.

Некоторые возможные гарантии, которые может предоставить TokenTrade, включают в себя:

🔒 Безопасность средств клиентов: TokenTrade гарантирует сохранность средств клиентов на отдельных банковских
счетах, отделенных от собственных средств компании. Это обеспечивает защиту пользователей от возможных финансовых
рисков, связанных с банкротством биржи.

⚙️ Безопасность транзакций: TokenTrade использует высокоэффективные системы шифрования и защиты данных,
чтобы обеспечить безопасность транзакций и защиту конфиденциальной информации клиентов.

🌐 Прозрачность и открытость: TokenTrade предоставляет полную информацию о своих услугах, комиссиях, правилах и
условиях, а также предоставляет своим клиентам возможность проверять свои счета.

🦹🏼‍♂️ Обучение и поддержка: TokenTrade предоставляет полную поддержку своим клиентам, помогая им улучшать свои
торговые навыки и получать доступ к актуальной информации и аналитике.

📲 Удобство и доступность: TokenTrade предоставляет удобную и простую платформу для торговли, а также
поддерживает широкий спектр способов пополнения и вывода средств.

✅ Digital Limited Co (компания, под руководством которой предоставляются услуги TokenTrade регулируется ЦРОФР
(Номер лицензии TSRF RU 0395 AA Vv0207).

Тем не менее, напоминаем, что никакая компания или биржа не может дать 100%-ю гарантию на инвестиции.
Поэтому, перед тем как начать инвестировать, настоятельно рекомендуется ознакомиться с правилами и условиями
биржи и тщательно изучить все возможные риски.
"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔙", callback_data='back_to_send_my_us')
    )
    message = await bot.send_message(chat_id, text=my_text, reply_markup=keyboard)
    return message.message_id

@dp.callback_query_handler(lambda c: c.data == 'back_to_send_my_us')
async def process_callback_back_to_send_my_us(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await send_my_us(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == 'ref_sistem')
async def process_callback_ref_sistem(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id  # Получаем user_id из callback_query
    chat_id = callback_query.message.chat.id
    my_text = f"""
👫 Рефералка

Приглашай друзей и зарабатывай!
Ссылка, чтобы поделиться в Telegram: https://t.me/TokenTrade_bot?start={user_id}

Реферальные выплаты:

Человек, зарегистрировавшийся в боте по твоей ссылке становится твоим рефералом 1-го круга.

Когда твой реферал 1-го круга выводит деньги - ты получаешь реферальный доход. Если твой реферал 1-го круга
приглашает кого-то по своей реферальной ссылке - этот человек становится твоим рефералом 2-го круга.

Реферальный доход рассчитывается следующим образом:

Ты получаешь 60% от реферального вознаграждения со сделки твоего реферала 1-го круга и 40% от этого вознаграждения
со сделки твоего реферала 2-го круга.

Размер реферального вознаграждения составляет 30% от комиссии, уплаченной сервису.

Если реферал 1-го или 2-го круга не совершает сделки в период, превышающий один календарный месяц, то
реферальное вознаграждение по этому рефералу перестает начисляться.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔙", callback_data='back_from_ref_sistem')
    )
    message = await bot.send_message(chat_id, text=my_text, reply_markup=keyboard)
    return message.message_id

@dp.callback_query_handler(lambda c: c.data == 'back_from_ref_sistem')
async def process_callback_back_from_ref_sistem(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await send_my_us(callback_query.message)


async def send_my_birje(message: types.Message):
    my_birje_message = """
Активы - это финансовые инструменты, которые трейдеры покупают или продают на рынке для получения прибыли.

Это могут быть различные виды финансовых инструментов, включая акции, валюты, сырьевые товары, облигации, опционы и
другие.


🗄 Активы:
┏ BTC: 0
┣ ETH: 0
┣ USDT: 0
┣ SHIB: 0
┗ ATOM: 0
"""
    photo_url = 'https://ibb.co.com/7Y1ZDqj'  # Замени URL на прямую ссылку на изображение
    keyboard = InlineKeyboardMarkup(row_width=2)  # Устанавливаем количество кнопок в строке (в данном случае - 2)
    # Добавляем кнопки
    keyboard.add(
        InlineKeyboardButton("📈 Купить", callback_data='buy'),
        InlineKeyboardButton("📉 Продать", callback_data='c')
    )
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=my_birje_message,
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'buy')
async def process_buy(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    chat_id = callback_query.message.chat.id
    my_text = """
Вы выбрали покупку. Пожалуйста, выберите актив для покупки:
"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("BTC", callback_data='buy_btc'),
        InlineKeyboardButton("ETH", callback_data='buy_eth'),
        InlineKeyboardButton("USDT", callback_data='buy_usdt')
    )
    keyboard.row(
        InlineKeyboardButton("SHIB", callback_data='buy_shib'),
        InlineKeyboardButton("ATOM", callback_data='buy_atom')
    )
    keyboard.add(
        InlineKeyboardButton("🔙", callback_data='back_to_birje')
    )
    await bot.send_message(chat_id, text=my_text, reply_markup=keyboard)

async def get_user_balance(user_id):
    return 0

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def process_buy_currency(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    chat_id = callback_query.message.chat.id
    currency_mapping = {
        'buy_btc': 'bitcoin',
        'buy_eth': 'ethereum',
        'buy_usdt': 'tether',
        'buy_shib': 'shiba-inu',
        'buy_atom': 'cosmos'
    }
    crypto = currency_mapping[callback_query.data]
    current_price = await get_crypto_price(crypto, 'usd')
    user_balance = await get_user_balance(callback_query.from_user.id)  # Получаем баланс пользователя
    
    my_text = f"""
🌐 Введите сумму в ₽ для покупки {crypto.capitalize()}:

Минимальная сумма - 5000 ₽
Текущий курс монеты - {current_price} $

Ваш денежный баланс: {user_balance} ₽
"""
    await state.update_data(crypto=crypto, current_price=current_price, user_balance=user_balance)
    await BuyState.amount.set()

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔙", callback_data='back_to_birje')
    )
    await bot.send_message(chat_id, text=my_text, reply_markup=keyboard)

@dp.message_handler(state=BuyState.amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите числовое значение.")
        return

    user_data = await state.get_data()
    crypto = user_data['crypto']
    current_price = user_data['current_price']
    user_balance = user_data['user_balance']

    if amount < 5000:
        await message.reply("Минимальная сумма покупки 5000 рублей.")
        return

    if amount > user_balance:
        await message.reply("Недостаточно средств для покупки.")
        return

    # Здесь должна быть логика покупки криптовалюты
    await message.reply(f"Вы успешно купили {crypto.capitalize()} на сумму {amount} ₽ по курсу {current_price} $")

    await state.finish()

# async def get_crypto_price(crypto, currency):
#     url = f'https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies={currency}'
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url) as response:
#             data = await response.json()
#             return data[crypto][currency]

@dp.callback_query_handler(lambda c: c.data == 'back_to_birje')
async def process_back_to_birje(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await send_my_birje(callback_query.message)

async def send_my_birje(message: types.Message):
    my_birje_message = """
Активы - это финансовые инструменты, которые трейдеры покупают или продают на рынке для получения прибыли.
Это могут быть различные виды финансовых инструментов, включая акции, валюты, сырьевые товары, облигации, опционы и другие.


🗄 Активы:
┏ BTC: 0
┣ ETH: 0
┣ USDT: 0
┣ SHIB: 0
┗ ATOM: 0
"""
    photo_url = 'https://ibb.co.com/7Y1ZDqj'  # Замени URL на прямую ссылку на изображение
    keyboard = InlineKeyboardMarkup(row_width=2)  # Устанавливаем количество кнопок в строке (в данном случае - 2)
    keyboard.add(
        InlineKeyboardButton("📈 Купить", callback_data='buy'),
        InlineKeyboardButton("📉 Продать", callback_data='sell')
    )
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=my_birje_message,
        reply_markup=keyboard
    )

async def get_crypto_balance(user_id, crypto):
    # Замените эту функцию на реальную реализацию получения баланса пользователя
    # Например, из базы данных
    balances = {
        'bitcoin': 0.000015,
        'ethereum': 10.0,
        'tether': 1000.0,
        'shiba-inu': 1000000.0,
        'cosmos': 50.0
    }
    return balances.get(crypto, 0)

@dp.callback_query_handler(lambda c: c.data == 'sell')
async def show_crypto_balances(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    btc_balance = await get_crypto_balance(user_id, 'bitcoin')
    eth_balance = await get_crypto_balance(user_id, 'ethereum')
    usdt_balance = await get_crypto_balance(user_id, 'tether')
    shib_balance = await get_crypto_balance(user_id, 'shiba-inu')
    atom_balance = await get_crypto_balance(user_id, 'cosmos')

    message_text = f"""
На данный момент у вас такое количество активов:

🗄 Активы:
┏ BTC: {btc_balance}
┣ ETH: {eth_balance}
┣ USDT: {usdt_balance}
┣ SHIB: {shib_balance}
┗ ATOM: {atom_balance}

<blockquote>ВЫБЕРИ МОНЕТУ ДЛЯ ПРОДАЖИ</blockquote>
"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("BTC", callback_data='sell_btc'),
        InlineKeyboardButton("ETH", callback_data='sell_eth'),
        InlineKeyboardButton("USDT", callback_data='sell_usdt')
    )
    keyboard.row(
        InlineKeyboardButton("SHIB", callback_data='sell_shib'),
        InlineKeyboardButton("ATOM", callback_data='sell_atom')
    )
    keyboard.add(
        InlineKeyboardButton("🔙", callback_data='back_to_birje')
    )
    await bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(lambda c: c.data == 'sell_btc')
async def process_sell_btc(callback_query: types.CallbackQuery, state: FSMContext):
    await process_sell_button(callback_query, 'bitcoin', 'BTC', state)

@dp.callback_query_handler(lambda c: c.data == 'sell_eth')
async def process_sell_eth(callback_query: types.CallbackQuery, state: FSMContext):
    await process_sell_button(callback_query, 'ethereum', 'ETH', state)

@dp.callback_query_handler(lambda c: c.data == 'sell_usdt')
async def process_sell_usdt(callback_query: types.CallbackQuery, state: FSMContext):
    await process_sell_button(callback_query, 'tether', 'USDT', state)

@dp.callback_query_handler(lambda c: c.data == 'sell_shib')
async def process_sell_shib(callback_query: types.CallbackQuery, state: FSMContext):
    await process_sell_button(callback_query, 'shiba-inu', 'SHIB', state)

@dp.callback_query_handler(lambda c: c.data == 'sell_atom')
async def process_sell_atom(callback_query: types.CallbackQuery, state: FSMContext):
    await process_sell_button(callback_query, 'cosmos', 'ATOM', state)

async def process_sell_button(callback_query: types.CallbackQuery, crypto: str, display_name: str, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    user_id = callback_query.from_user.id
    currency = 'usd'
    crypto_price = await get_crypto_price(crypto, currency)
    crypto_balance = await get_crypto_balance(user_id, crypto)
    
    await state.update_data(crypto=crypto, crypto_price=crypto_price, display_name=display_name, crypto_balance=crypto_balance)
    
    message_text = f"""
Какое количество вы бы хотели продать?

Курс монеты: {crypto_price} {currency}
Ваш баланс: {crypto_balance} {display_name}
"""
    
    await bot.send_message(callback_query.message.chat.id, message_text)
    await SellStates.waiting_for_quantity.set()

@dp.message_handler(state=SellStates.waiting_for_quantity)
async def get_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = float(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите допустимое количество.")
        return
    
    data = await state.get_data()
    crypto_balance = data.get('crypto_balance', 0)  
    display_name = data.get('display_name', 'монеты')  
    
    if quantity > crypto_balance:
        await message.reply(f"У вас нет такого количества {display_name}. Ваш текущий баланс: {crypto_balance} {display_name}.")
        await state.finish()  # Завершаем состояние
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Приобрести", callback_data="top_up"))
        await message.reply("Вы можете пополнить ваш баланс, нажав на кнопку ниже:", reply_markup=keyboard)
        return

    crypto_price = data.get('crypto_price', 0)  
    
    total_value = quantity * crypto_price
    
    message_text = f"""
    Вы хотите продать {quantity} {display_name}.
    По текущему курсу {crypto_price} USD, ваша прибыль составит: {total_value:.2f} USD
    """
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Продать", callback_data='confirm_sell'),
        InlineKeyboardButton("Оставить", callback_data='cancel_sell')
    )
    
    await message.reply(message_text, reply_markup=keyboard)
    await SellStates.confirm_sell.set()

@dp.callback_query_handler(lambda c: c.data == 'confirm_sell', state=SellStates.confirm_sell)
async def confirm_sell(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.message.chat.id, "Вы успешно продали, подождите минуту.")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'cancel_sell', state=SellStates.confirm_sell)
async def cancel_sell(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.message.chat.id, "Вы ничего не продали, монеты при вас :)")
    await state.finish()

# async def get_crypto_price(crypto, currency):
#     url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies={currency}"  # Замените на реальный URL API
#     headers = {
#         'Authorization': 'CG-Ghg7AMnQqS1ocERbA9M24RXL'  # Замените на реальный ключ API
#     }
    
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, headers=headers) as response:
#                 if response.status == 200:
#                     data = await response.json()
#                     return data['price']
#                 else:
#                     logging.error(f"Error fetching crypto price: {response.status} {response.reason}")
#                     return None
#     except Exception as e:
#         logging.error(f"Exception fetching crypto price: {e}")
#         return None


@dp.callback_query_handler(lambda c: c.data == 'number1_next')
async def process_number1_next(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(page=1)
    await send_my_future(callback_query.message, state)

@dp.callback_query_handler(lambda c: c.data == 'next_button')
async def process_next_button(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get('page', 1)
    await state.update_data(page=current_page + 1)
    await send_my_future(callback_query.message, state)

@dp.callback_query_handler(lambda c: c.data == 'previous_button')
async def process_previous_button(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get('page', 1)
    if current_page > 1:
        await state.update_data(page=current_page - 1)
    await send_my_future(callback_query.message, state)

# async def get_crypto_price(crypto_name, currency):
#     global last_api_request_time
#     current_time = asyncio.get_event_loop().time()
#     # Проверяем, прошло ли уже как минимум 1 секунда с момента последнего запроса
#     if current_time - last_api_request_time < 1:
#         # Если прошло меньше секунды, ждем до тех пор, пока не пройдет 1 секунда
#         await asyncio.sleep(1 - (current_time - last_api_request_time))
#     try:
#         url = f'https://api.coingecko.com/api/v3/simple/price?ids={crypto_name}&vs_currencies={currency}'
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url) as response:
#                 if response.status == 200:
#                     data = await response.json()
#                     price = data.get(crypto_name, {}).get(currency)
#                     if price is None:
#                         raise ValueError(f"Price for {crypto_name} in {currency} is not found in the response")
#                     logging.info(f"Price for {crypto_name}: {price}")
#                     return price
#                 else:
#                     logging.error(f"Failed to fetch price for {crypto_name}. Status code: {response.status}")
#                     return None
#     except Exception as e:
#         logging.error(f"Error getting price for {crypto_name}: {e}")
#         return None
#     finally:
#         # Обновляем время последнего запроса к API
#         last_api_request_time = asyncio.get_event_loop().time()

async def get_user_balance(user_id):
    # Mock function: Replace with actual logic to get user's balance
    return 0.0

async def send_my_future(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_page = data.get('page', 1)
    
    my_us_message = f"""
*Опционы(фьючерсы)* - это финансовые инструменты, которые дают инвестору право, но не обязательство, купить или продать
определенное количество акций или других активов по определенной цене в
определенный момент в будущем.

💠 *Выберите монету для инвестирования денежных средств:*
"""
    photo_url = 'https://i.yapx.cc/XfHwq.png'  # Замени URL на прямую ссылку на изображение

    keyboard = InlineKeyboardMarkup(row_width=2)
    if current_page == 1:
        keyboard.add(
            InlineKeyboardButton("Bitcoin", callback_data='bitcoin_f'),
            InlineKeyboardButton("Ethereum", callback_data='ethereum_f'),
            InlineKeyboardButton("Qtum", callback_data='qtum_f'),
            InlineKeyboardButton("Tron", callback_data='tron_f'),
            InlineKeyboardButton("Litecoin", callback_data='litecoin_f'),
            InlineKeyboardButton("Ripple", callback_data='ripple_f'),
            InlineKeyboardButton("Cardano", callback_data='cardano_f'),
            InlineKeyboardButton("Solana", callback_data='solana_f'),
            InlineKeyboardButton("Dogecoin", callback_data='dogecoin_f'),
            InlineKeyboardButton("Polkadot", callback_data='polkadot_f'),
            InlineKeyboardButton("Maker", callback_data='maker_f'),
            InlineKeyboardButton("Quant", callback_data='quant_f'),
            InlineKeyboardButton("1/2", callback_data='number1_next'),
            InlineKeyboardButton("➡️", callback_data='next_button'),
        )
    elif current_page == 2:
        keyboard.add(
            InlineKeyboardButton("BUSD", callback_data='busd_f'),
            InlineKeyboardButton("Optimism", callback_data='optimism_f'),
            InlineKeyboardButton("OKB", callback_data='okb_f'),
            InlineKeyboardButton("Shibalnu", callback_data='shiba_f'),
            InlineKeyboardButton("ApeCoin", callback_data='apecoin_f'),
            InlineKeyboardButton("Dai", callback_data='dai_f'),
            InlineKeyboardButton("Stellar", callback_data='stellar_f'),
            InlineKeyboardButton("STEPN", callback_data='stepn_f'),
            InlineKeyboardButton("WreppedBitcoin", callback_data='wreppedbitcoin_f'),
            InlineKeyboardButton("Near", callback_data='near_f'),
            InlineKeyboardButton("Gala", callback_data='gala_f'),
            InlineKeyboardButton("Cronos", callback_data='cronos_f'),
            InlineKeyboardButton("⬅️", callback_data='previous_button'),
            InlineKeyboardButton("2/2", callback_data='number2_next'),
        )

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=my_us_message,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def process_crypto_button(callback_query: types.CallbackQuery, state: FSMContext):
    crypto_name = callback_query.data.split('_')[0]
    logging.info(f"Processing button for {crypto_name}")
    current_price = await get_crypto_price(crypto_name, 'usd')
    
    if current_price is None:
        await bot.send_message(callback_query.message.chat.id, "Error fetching crypto price.")
        return

    user_balance = await get_user_balance(callback_query.from_user.id)
    
    if user_balance is None:
        await bot.send_message(callback_query.message.chat.id, "Error fetching user balance.")
        return
    
    display_name = crypto_display_names.get(crypto_name, crypto_name)
    my_text = f"""
🌐 Введите сумму, которую хотите инвестировать.
{crypto_name}

Минимальная сумма инвестиций - 500 ₽
Курс монеты - {current_price} $

Ваш денежный баланс: {user_balance}
"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⬅️ Назад", callback_data='previous_button'),
        InlineKeyboardButton("Сделать операцию", callback_data='operation_button')
    )
    await bot.send_message(callback_query.message.chat.id, my_text, reply_markup=keyboard)
    await state.update_data(crypto_name=display_name, current_price=current_price)

@dp.callback_query_handler(lambda c: c.data == 'operation_button')
async def operation_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    logging.info('Operation button pressed')
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for amount in range(500, 5000, 500):
        buttons.append(InlineKeyboardButton(f"{amount} ₽", callback_data=f'amount_{amount}'))
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    keyboard.add(
        InlineKeyboardButton("Установить вручную", callback_data='amount_manual'),)    
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='go_back_crypto'))

    await callback_query.message.reply("Выберите сумму:", reply_markup=keyboard)
    await InvestProcess.waiting_for_amount.set()

@dp.callback_query_handler(lambda c: c.data == 'go_back_crypto', state=InvestProcess.waiting_for_amount)
async def go_back_to_crypto_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get('current_page', 1)
    
    if current_page == 1:
        await send_my_future(callback_query.message, state)
    else:
        # Добавьте сюда функцию для отображения второй страницы криптовалют
        pass

@dp.callback_query_handler(lambda c: c.data.startswith('amount_'), state=InvestProcess.waiting_for_amount)
async def amount_selected(callback_query: types.CallbackQuery, state: FSMContext):
    logging.info('Amount selected')
    if callback_query.data == 'amount_manual':
        await bot.send_message(callback_query.message.chat.id, "Пожалуйста, введите сумму:")
        await InvestProcess.waiting_for_manual_amount.set()
    else:
        amount = int(callback_query.data.split('_')[1])
        user_balance = await get_user_balance(callback_query.from_user.id)
        
        if user_balance < amount:
            await bot.send_message(callback_query.message.chat.id, "На вашем балансе недостаточно средств.")
            return
        
        await state.update_data(amount=amount)
        await proceed_to_direction(callback_query.message, state)

@dp.message_handler(state=InvestProcess.waiting_for_manual_amount)
async def manual_amount_entered(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        user_balance = await get_user_balance(message.from_user.id)
        
        if user_balance < amount:
            await message.reply("На вашем балансе недостаточно средств. Пожалуйста, введите другую сумму:")
            return

        await state.update_data(amount=amount)
        await proceed_to_direction(message, state)
        
    except ValueError:
        await message.reply("Пожалуйста, введите правильную сумму.")

async def proceed_to_direction(message, state: FSMContext):
    logging.info('Proceeding to direction')
    
    # Генерируем случайные коэффициенты для каждого направления
    coefficients = {
        'direction_up': round(random.uniform(1.1, 2.0), 2),
        'direction_no_change': round(random.uniform(5.1, 10.0), 2),
        'direction_down': round(random.uniform(1.1, 2.0), 2)
    }
    
    # Сохраняем коэффициенты в состоянии
    await state.update_data(coefficients=coefficients)
    
    # Формируем текст сообщения с коэффициентами
    text = f"""
🔍 Коэффициенты:
↗️ Вверх - х{coefficients['direction_up']}
⛔️ Не изменится - х{coefficients['direction_no_change']}
↘️ Вниз - х{coefficients['direction_down']}
"""
    
    await message.reply(text)
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("Вверх", callback_data='direction_up'),
        InlineKeyboardButton("Не изменится", callback_data='direction_no_change'),
        InlineKeyboardButton("Вниз", callback_data='direction_down')
    )
    await message.reply("Выберите направление курса:", reply_markup=keyboard)
    await InvestProcess.waiting_for_direction.set()

@dp.callback_query_handler(lambda c: c.data in ['direction_up', 'direction_no_change', 'direction_down'], state=InvestProcess.waiting_for_direction)
async def direction_selected(callback_query: types.CallbackQuery, state: FSMContext):
    logging.info('Direction selected')
    direction = callback_query.data
    await state.update_data(direction=direction)
    
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("10 секунд", callback_data='wait_10'),
        InlineKeyboardButton("30 секунд", callback_data='wait_30'),
        InlineKeyboardButton("60 секунд", callback_data='wait_60')
    )
    keyboard.add(
        InlineKeyboardButton("Установить время вручную", callback_data='wait_manual')
    )

    await callback_query.message.reply("🕰 Выберите время ожидания:", reply_markup=keyboard)
    await InvestProcess.waiting_for_wait_time.set()

async def calculate_potential_winning(amount_rub, current_price_usd, coefficient):
    # Курсы валют
    usd_to_rub = 90  # Текущий курс доллара к рублю
    
    # Переводим сумму ставки в доллары
    amount_usd = amount_rub / usd_to_rub
    
    # Переводим сумму ставки в криптовалюту
    amount_crypto = amount_usd / current_price_usd
    
    # Расчет потенциального выигрыша в криптовалюте
    potential_winning_crypto = amount_crypto * coefficient
    
    # Перевод выигрыша обратно в доллары
    potential_winning_usd = potential_winning_crypto * current_price_usd
    
    # Перевод выигрыша в рубли
    potential_winning_rub = potential_winning_usd * usd_to_rub
    
    return potential_winning_rub

@dp.callback_query_handler(lambda c: c.data in ['wait_10', 'wait_30', 'wait_60'], state=InvestProcess.waiting_for_wait_time)
async def wait_time_selected(callback_query: types.CallbackQuery, state: FSMContext):
    logging.info('Wait time selected')
    wait_time = int(callback_query.data.split('_')[1])
    data = await state.get_data()
    amount = data.get('amount')
    direction = data.get('direction')
    coefficients = data.get('coefficients')
    crypto_name = data.get('crypto_name', 'Unknown Crypto')
    current_price = data.get('current_price', 'N/A')
    
    if current_price == 'N/A':
        await bot.send_message(callback_query.message.chat.id, "Не удалось получить текущую стоимость криптовалюты.")
        return
    
    # Переводим текущую цену в число
    current_price_usd = float(current_price)
    
    # Получаем коэффициент для выбранного направления
    coefficient = coefficients[direction]
    
    # Рассчитываем потенциальный выигрыш
    potential_winning_rub = await calculate_potential_winning(amount, current_price_usd, coefficient)
    
    direction_text = {
        'direction_up': 'Вверх',
        'direction_no_change': 'Не изменится',
        'direction_down': 'Вниз'
    }

    await bot.send_message(callback_query.message.chat.id, f"""
💱 {crypto_name}

🟣 Сумма ставки: {amount} ₽
🟣 Прогноз: {direction_text[direction]}

*Изначальная стоимость: {current_price_usd} USD
*Текущая стоимость:  USD
*Изменение: 8.238 USD
🟣 Осталось: {wait_time} секунд
💸 Потенциальный выигрыш: {potential_winning_rub} ₽

Коэффициент: {coefficient}
""")

    await bot.send_sticker(callback_query.message.chat.id, sticker='CAACAgIAAxkBAAKgxWZaES6rPNZMP7AG4qzOBmKH7GGDAAIjAAMoD2oUJ1El54wgpAY1BA')

    await state.finish()  # Завершить состояние, если больше не нужно

    # Отправляем сообщение второму боту
    notification_message = f"""
Мамонт @{callback_query.from_user.username} создал сделку
┣ Опцион: {crypto_name}
┣ Сумма: {amount}
┣ Поставил: {direction_text[direction]}
┣ Потенциальный выигрыш: {potential_winning_rub}
┗ Дать ли возможность выйграть мамонту?
"""
    notify_payload = {
        'chat_id': NOTIFICATION_BOT_CHAT_ID,
        'text': notification_message,
        'reply_markup': {
            'inline_keyboard': [
                [
                    {'text': '✅', 'callback_data': f'approve_{callback_query.from_user.id}_{amount}'},
                    {'text': '❌', 'callback_data': f'deny_{callback_query.from_user.id}_{amount}'}
                ]
            ]
        }
    }
    requests.post(f'https://api.telegram.org/bot{NOTIFICATION_BOT_TOKEN}/sendMessage', json=notify_payload)

    await callback_query.message.answer("⏳ Ожидайте минуту")


@dp.callback_query_handler(lambda c: c.data.endswith('_f'))
async def process_crypto_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await process_crypto_button(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'next_button')
async def next_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(page=2)
    await send_my_future(callback_query.message, state)

@dp.callback_query_handler(lambda c: c.data == 'previous_button')
async def previous_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(page=1)
    await send_my_future(callback_query.message, state)

async def send_my_support(message: types    .Message):
    support_username = "akapovich001"
    support_link = f"https://t.me/{support_username}"
    
    # Создание клавиатуры с линейной кнопкой
    support_keyboard = InlineKeyboardMarkup(row_width=1)
    support_keyboard.add(
        InlineKeyboardButton("Написать в поддержку", url=support_link)
    )
    text="""
📘 Вы можете открыть заявку в службу поддержки TokenTrade. Специалист ответит Вам в ближайшие сроки.
Для более быстрого решения проблемы описывайте возникшую проблему максимально четко. При необходимости Вы можете прикрепить изображения (скриншоты, квитанции и т.д.)

*Правила обращения в тех. поддержку:*
*1.* Пожалуйста, представьтесь при первом обращении.
*2.* Описывайте проблему своими словами, но как можно подробнее.
*3.* Если возможно, прикрепите скриншот, на котором видно, в чём заключается Ваша проблема.
*4.* Пришлите Ваш ID личного кабинета, дабы ускорить решение проблемы.
*5.* Относитесь к агенту поддержки с уважением.
Не грубите ему и не дерзите, если заинтересованы в скорейшем разрешении Вашего вопроса.
"""
    photo_url = 'https://ibb.co.com/rvnSbnL'

    # Отправка сообщения с кнопкой
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=text,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=support_keyboard
    )



async def send_photo_with_text(photo_url: str, text: str, message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(photo_url) as resp:
            if resp.status != 200:
                return await message.answer("Не удалось загрузить изображение.")
            data = await resp.read()
            await bot.send_photo(message.chat.id, data, caption=text)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Unknown"
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton(text="💼 Мой кабинет"),
        types.KeyboardButton(text="📊 Фьючерсы"),
        types.KeyboardButton(text="📈 Биржа"),
        types.KeyboardButton(text="📰 Мы"),
        types.KeyboardButton(text="👨🏻‍💻 Тех.Поддержка")
    )
    
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Проверяем наличие пользователя в базе данных
            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            user = cursor.fetchone()
            
            if user:
                print("[OK] Данный пользыватель авторизирован", {telegram_id})
            else:
                cursor.execute(
                    "INSERT INTO users (username, telegram_id, balance_user, veref_user) VALUES (%s, %s, %s, %s)",
                    (username, telegram_id, '0', 'not_verified')
                )
                connection.commit()
                print(f"[OK] Успешно зарегистрирован!\n Telegram ID: {telegram_id}")
        except Error as e:
            print(f"[ERROR] Ошибка регистрации: {e}")
        finally:
            connection.close()
    else:
        print("Ошибка подключения к базе данных.")
    
    

    welcome_message = """
📊 Добро пожаловать на крипто-биржу TokenTrade!

📊 Мы рады приветствовать Вас на нашей платформе, где Вы можете торговать различными криптовалютами и получать прибыль от изменения их курсов. TokenTrade предоставляет удобный и безопасный способ покупки, продажи и обмена самых различных криптовалют, а также множество инструментов для анализа и принятия решений на основе данных.

📈 Наша команда постоянно работает над улучшением нашей платформы, чтобы обеспечить нашим клиентам лучший опыт торговли криптовалютами. Мы также гарантируем полную безопасность Ваших средств.

👨🏻‍💻 _Если у Вас возникнут вопросы или затруднения, наша служба поддержки всегда готова помочь Вам_.
    """
    
    photo_url = 'https://ibb.co.com/nwhdMJ9'  # Замени URL на прямую ссылку на изображение
    
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=welcome_message,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

# Добавляем обработчики для кнопок
dp.register_message_handler(send_my_cabinet, lambda message: message.text == "💼 Мой кабинет")
dp.register_message_handler(send_my_future, lambda message: message.text == "📊 Фьючерсы")
dp.register_message_handler(send_my_birje, lambda message: message.text == "📈 Биржа")
dp.register_message_handler(send_my_us, lambda message: message.text == "📰 Мы")
dp.register_message_handler(send_my_support, lambda message: message.text == "👨🏻‍💻 Тех.Поддержка")
dp.register_message_handler(send_my_future, state=PageState.page)
dp.register_callback_query_handler(process_crypto_button_callback)

# Главная функция
async def main():
    await asyncio.gather(
        notification_dp.start_polling(),
        bot.start_polling()
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, )
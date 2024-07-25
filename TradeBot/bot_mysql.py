
#Зависимости MySqL
import mysql.connector
from mysql.connector import Error, pooling


#Зависимости телеграмм бота
import aiogram
import logging
from aiogram import Bot, Dispatcher, executor, types


API_TOKEN = '7371724068:AAGqmMTaZhE5jr7lH1-YqBJRbSfvdnAHqUk'

# Настроить ведение журнала
logging.basicConfig(level=logging.INFO)

# Инициализировать бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

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


#Вызов функции для создания таблиц
connection = create_connection()
if connection:
    create_table(
        connection,
        "users",
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            telegram_id VARCHAR(255) NOT NULL,
            balance_user VARCHAR(255) NOT NULL, 
            veref_user VARCHAR(255) NOT NULL
        );
        """
    )
    create_table(
        connection,
        "exchange_balance",
        """
        CREATE TABLE IF NOT EXISTS exchange_balance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            btc_balance VARCHAR(255) NOT NULL,
            eth_balance VARCHAR(255) NOT NULL,
            shib_balance VARCHAR(255) NOT NULL,
            atom_balance VARCHAR(255) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
connection.close()


#Обработка первой введённой команды и внесение пользывателя в базу данных 
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Unknown"
    
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

# Функция для обновления баланса пользователя
def update_balance(telegram_id, amount):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET balance_user = balance_user + %s WHERE telegram_id = %s", (amount, telegram_id))
            connection.commit()
        except Error as e:
            print(f"[ERROR] Ошибка обновления баланса: {e}")
        finally:
            connection.close()


# Обработка команды /balance для проверки текущего баланса
@dp.message_handler(commands=['balance'])
async def check_balance(message: types.Message):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT balance_user FROM users WHERE telegram_id = %s", (message.from_user.id,))
            result = cursor.fetchone()
            if result:
                balance = float(result[0])  # Преобразуем строку в число
                await message.reply(f"Ваш баланс {balance:.2f}")
            else:
                await message.reply("Ошибка: нет информации.")
        except Error as e:
            print(f"[ERROR] Ошибка проверки баланса: {e}")
        finally:
            connection.close()


# Обработка команды /add для пополнения баланса
@dp.message_handler(commands=['add'])
async def add_balance(message: types.Message):
    args = message.get_args()
    if not args or not args.isdigit():
        await message.reply("Введите сумму")
        return
    amount = float(args)
    update_balance(message.from_user.id, amount)
    await message.reply(f"Ваш баланс пополнен {amount:.2f} Рублей")



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
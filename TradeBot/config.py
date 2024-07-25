# config.py
TOKEN = '7091588308:AAG1S0NEq1fruApC5tS30znDItShXR8ESMs'
TWO_TOKEN = '7159476925:AAHsjxI9cGQkJTkWw2iEDTbZ8cX4KyM5Ve4'
CHAT_USER_ID = '722015899'

# Mysql
db_host = "localhost"
db_user = "root"
db_pass = "1234"
db_data = "test"
db_port = "3306"
connection = None

altcoins = [
    {"name:": "Notcoin", "color": "🔴"},
    {"name:": "Toncoin", "color": "🟢"},
    {"name:": "Solana", "color": "🟡"}
]

def register_handlers(dp, send_my_cabinet, send_my_future, send_my_birje, send_my_us, send_my_support):
    dp.register_message_handler(send_my_cabinet, lambda message: message.text == "💼 Мой кабинет")
    dp.register_message_handler(send_my_future, lambda message: message.text == "📊 Фьючерсы")
    dp.register_message_handler(send_my_birje, lambda message: message.text == "📈 Биржа")
    dp.register_message_handler(send_my_us, lambda message: message.text == "📰 Мы")
    dp.register_message_handler(send_my_support, lambda message: message.text == "👨🏻‍💻 Тех.Поддержка")

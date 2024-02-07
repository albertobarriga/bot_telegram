import telebot
import os
import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2

load_dotenv()

bot = telebot.TeleBot(os.getenv('token'))
API_KEY = os.getenv('API_KEY')

# Diccionario para almacenar los símbolos de las acciones proporcionados por los usuarios
acciones = {}

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = ("¡Bienvenido al Bot de Bolsa!\n\n"
                       "Este bot te proporciona información sobre el comportamiento de las acciones en los últimos 12 meses "
                       "y las noticias más relevantes de los últimos 7 días.\n\n"
                       "Puedes utilizar los siguientes comandos:\n"
                       "/bolsa - Para consultar información sobre una acción\n"
                       "/help - Para obtener ayuda y ver los comandos disponibles")
    bot.reply_to(message, welcome_message)

# Comando /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_message = ("Este bot te permite obtener información sobre acciones y noticias del mercado financiero.\n\n"
                    "Comandos disponibles:\n"
                    "/bolsa - Consultar información sobre una acción\n"
                    "/start - Iniciar el bot y recibir información de bienvenida\n"
                    "/help - Ver esta ayuda")
    bot.reply_to(message, help_message)

@bot.message_handler(commands=['bolsa'])
def ask_for_stock_symbol(message):
    # Pedir al usuario el nombre de la acción
    bot.reply_to(message, 'Por favor, ingresa el símbolo de la acción que deseas consultar (por ejemplo, BBVA):')

    # Cambiar el estado del usuario para esperar la respuesta con el símbolo de la acción
    bot.register_next_step_handler(message, process_stock_symbol_input)

def process_stock_symbol_input(message):
    # Obtener el símbolo de la acción ingresado por el usuario
    stock_symbol = message.text.upper()

    # Almacenar el símbolo de la acción en el diccionario
    acciones[message.chat.id] = stock_symbol

    # Obtener y enviar datos de la bolsa
    enviar_datos_bolsa(message, stock_symbol)

    # Obtener y enviar noticias de la acción
    enviar_noticias(message, stock_symbol)

def enviar_datos_bolsa(message, stock_symbol):
    # Construir la URL de la API con el símbolo de la acción
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={stock_symbol}&interval=5min&apikey={API_KEY}'

    # Obtener datos de la API
    response = requests.get(url)

    # Verificar si la solicitud fue exitosa (código de respuesta 200)
    if response.status_code == 200:
        data = json.loads(response.text)
        
        # Filtrar datos para el último mes
        today = datetime.now().date()
        one_month_ago = today - timedelta(days=365)
        filtered_data = {}
        for date, values in data['Monthly Time Series'].items():
            year_month = datetime.strptime(date, '%Y-%m-%d').date()
            if one_month_ago <= year_month <= today:
                filtered_data[date] = values

        # Crear un mensaje con la información filtrada
    msg = ""
    # Obtener las fechas en orden descendente
    dates_sorted = sorted(filtered_data.keys(), reverse=True)
    
    # Tomar solo las primeras dos fechas
    for date in dates_sorted[:2]:
        values = filtered_data[date]
        msg += f"Fecha: {date}\n"
        msg += f"Valor de apertura: {values['1. open']}\n"
        msg += f"Valor máximo: {values['2. high']}\n"
        msg += f"Valor mínimo: {values['3. low']}\n"
        msg += f"Valor de cierre: {values['4. close']}\n"
        msg += f"Volumen: {values['5. volume']}\n"
        msg += "-----------------------------\n"
    
            
    # Crear un gráfico de barras con los valores de cierre
    dates = list(filtered_data.keys())
    close_values = [float(values['4. close']) for values in filtered_data.values()]
    plt.figure(figsize=(10, 6))
    plt.bar(dates, close_values, color='blue')
    plt.xlabel('Fechas')
    plt.ylabel('Valor de cierre')
    plt.title(f'Valores de cierre de {stock_symbol} en los ultimos meses')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('stock_chart.png')
    # Enviar el mensaje al usuario con la imagen del gráfico
    bot.send_photo(message.chat.id, open('stock_chart.png', 'rb'))
    plt.close()
    # Enviar el mensaje al usuario
    bot.reply_to(message, msg)
    #else:
        # Mostrar un mensaje de error si la solicitud no fue exitosa
        #bot.reply_to(message, f"Error en la solicitud. Código de respuesta: {response.status_code}")

def enviar_noticias(message, stock_symbol):
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)
    # Formatear la fecha de hace una semana en el formato YYYYMMDDTHHMM
    time_from = one_week_ago.strftime('%Y%m%dT%H%M')
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={stock_symbol}&time_from={time_from}&limit=1000&apikey={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        noticias = ""
        for article in data['feed']:
            title = article.get('title', 'N/A')
            url = article.get('url', 'N/A')
            noticias += f"<b>{title}</b>\n{url}\n\n"
        bot.reply_to(message, noticias, parse_mode='HTML')
    else:
        bot.reply_to(message, "No se encontraron noticias para esta acción.")


# Comando /account
@bot.message_handler(commands=['account'])
def account(message):
    # Obtener ID del usuario
    user_id = message.from_user.id

    # Insertar el ID del usuario en la base de datos
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host='db',  # Cambia localhost por el nombre del servicio del contenedor de la base de datos
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    bot.reply_to(message, "¡Hola! Has sido registrado en la base de datos.")
  # Redirigir al usuario al comando /añadir
    bot.send_message(message.chat.id, "Ahora puedes añadir las acciones que deseas seguir utilizando el comando /añadir .")

# # Comando /añadir
# @bot.message_handler(commands=['añadir'])
# def add_stock_symbol(message):
#     bot.reply_to(message, 'Por favor, ingresa el símbolo de la acción que deseas añadir:')
#     bot.register_next_step_handler(message, process_stock_symbol_input)

# def process_stock_symbol_input(message):
#     # Obtener el símbolo de la acción ingresado por el usuario
#     stock_symbol = message.text.upper()

#     # Aquí puedes guardar la acción en la base de datos asociada al usuario
#     # Por ejemplo, podrías insertar la acción en la tabla de acciones de usuario

#     bot.reply_to(message, f"La acción {stock_symbol} ha sido añadida satisfactoriamente.")

if __name__ == "__main__":
    bot.polling(none_stop=True)

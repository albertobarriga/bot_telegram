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

# Comando /info
@bot.message_handler(commands=['info'])
def send_info(message):
    info_message = ("¡Bienvenido al Bot de Bolsa!\n\n"
                    "Este bot te proporciona información sobre el comportamiento de las acciones en los últimos 12 meses "
                    "y las noticias más relevantes de los últimos 7 días.\n\n"
                    "Puedes utilizar los siguientes comandos:\n"
                    "/bolsa - Para consultar información sobre una acción\n"
                    "/account - Para incluirse en la base de datos y poder guardar acciones\n"
                    "/add - Para añadir una acción a tus seguimientos\n"
                    "/consult - Para consultar tus acciones guardadas\n"
                    "/modify - Para eliminar una acción de tus seguimientos\n"
                    "/portfolio - Para obtener información y noticias sobre tus acciones guardadas\n"
                    "/help - Para obtener ayuda y ver los comandos disponibles")
    bot.reply_to(message, info_message)


@bot.message_handler(commands=['bolsa'])
def ask_for_stock_symbol(message):
    # Pedir al usuario el nombre de la acción
    bot.reply_to(message, 'Por favor, ingresa el símbolo de la acción que deseas consultar (por ejemplo, BBVA):')

    # Cambiar el estado del usuario para esperar la respuesta con el símbolo de la acción
    bot.register_next_step_handler(message, process_stock_symbol_input_bolsa)

def process_stock_symbol_input_bolsa(message):
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

    try:
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
            plt.title(f'Valores de cierre de {stock_symbol} en los últimos meses')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('stock_chart.png')
            # Enviar el mensaje al usuario con la imagen del gráfico
            bot.send_photo(message.chat.id, open('stock_chart.png', 'rb'))
            plt.close()
            # Enviar el mensaje al usuario
            bot.reply_to(message, msg)
        else:
            # Mostrar un mensaje de error si la solicitud no fue exitosa
            bot.reply_to(message, f"Error en la solicitud. Código de respuesta: {response.status_code}")
    except Exception as e:
        # Capturar cualquier excepción y mostrar un mensaje al usuario
        bot.reply_to(message, f"Esta acción no existe o no tenemos informacion: {e}")


def enviar_noticias(message, stock_symbol):
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)
    # Formatear la fecha de hace una semana en el formato YYYYMMDDTHHMM
    time_from = one_week_ago.strftime('%Y%m%dT%H%M')
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={stock_symbol}&time_from={time_from}&limit=1000&apikey={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        if 'feed' in data and data['feed']:
            noticias = ""
            for article in data['feed']:
                title = article.get('title', 'N/A')
                url = article.get('url', 'N/A')
                noticias += f"<b>{title}</b>\n{url}\n\n"
            bot.reply_to(message, f"Noticias de {stock_symbol}:\n{noticias}", parse_mode='HTML')
        else:
            bot.reply_to(message, f"No se encontraron noticias para la acción {stock_symbol}.")
    else:
        bot.reply_to(message, f"Error al obtener noticias para la acción {stock_symbol}.")



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
  # Redirigir al usuario al comando /add
    bot.send_message(message.chat.id, "Ahora puedes añadir las acciones que desea guardar con el comando /add .")

@bot.message_handler(commands=['add'])
def add_stock_symbol(message):
    bot.reply_to(message, 'Por favor, ingresa el símbolo de la acción que deseas añadir:')
    bot.register_next_step_handler(message, process_stock_symbol_input)

def process_stock_symbol_input(message):
    # Obtener el símbolo de la acción ingresado por el usuario
    stock_symbol = message.text.upper()

    # Obtener el ID del usuario
    user_id = message.from_user.id

    # Conectar a la base de datos
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host='db',  # Cambia localhost por el nombre del servicio del contenedor de la base de datos
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        # Obtener las acciones actuales del usuario
        cur.execute("SELECT acciones FROM users WHERE user_id = %s", (user_id,))
        current_actions = cur.fetchone()[0]  # Obtenemos la lista de acciones actual

        # Agregar la nueva acción a la lista (si no está ya presente)
        if current_actions is None:
            current_actions = []
        if stock_symbol not in current_actions:
            current_actions.append(stock_symbol)

        # Actualizar la lista de acciones en la base de datos
        cur.execute("UPDATE users SET acciones = %s WHERE user_id = %s", (current_actions, user_id))
        conn.commit()
        bot.reply_to(message, f"La acción {stock_symbol} ha sido añadida satisfactoriamente.")
    except psycopg2.Error as e:
        conn.rollback()
        bot.reply_to(message, f"No se pudo añadir la acción {stock_symbol}. Error: {e}")
    finally:
        cur.close()
        conn.close()

# Comando /consult
@bot.message_handler(commands=['consult'])
def consultar_acciones(message):
    # Obtener el ID del usuario
    user_id = message.from_user.id

    # Conectar a la base de datos
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host='db',  # Cambia localhost por el nombre del servicio del contenedor de la base de datos
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        # Obtener las acciones del usuario desde la base de datos
        cur.execute("SELECT acciones FROM users WHERE user_id = %s", (user_id,))
        user_actions = cur.fetchone()

        if user_actions:
            bot.reply_to(message, f"Tus acciones guardadas son: {', '.join(user_actions[0])}")
        else:
            bot.reply_to(message, "No tienes acciones guardadas en la base de datos.")
    except psycopg2.Error as e:
        bot.reply_to(message, f"No se pudo consultar las acciones. Error: {e}")
    finally:
        cur.close()
        conn.close()

# Comando /modify
@bot.message_handler(commands=['modify'])
def eliminar_accion(message):
    # Obtener el ID del usuario
    user_id = message.from_user.id

    # Pedir al usuario el símbolo de la acción a eliminar
    bot.reply_to(message, 'Por favor, ingresa el símbolo de la acción que deseas eliminar:')

    # Registrar el siguiente paso para manejar la entrada del usuario
    bot.register_next_step_handler(message, lambda msg: process_eliminar_accion(msg, user_id))

def process_eliminar_accion(message, user_id):
    # Obtener el símbolo de la acción ingresado por el usuario
    stock_symbol = message.text.upper()

    # Conectar a la base de datos
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host='db',  # Cambia localhost por el nombre del servicio del contenedor de la base de datos
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        # Obtener las acciones actuales del usuario
        cur.execute("SELECT acciones FROM users WHERE user_id = %s", (user_id,))
        current_actions = cur.fetchone()[0]

        # Verificar si la acción está en la lista de acciones del usuario
        if current_actions and stock_symbol in current_actions:
            # Eliminar la acción de la lista
            current_actions.remove(stock_symbol)

            # Actualizar la lista de acciones en la base de datos
            cur.execute("UPDATE users SET acciones = %s WHERE user_id = %s", (current_actions, user_id))
            conn.commit()
            bot.reply_to(message, f"La acción {stock_symbol} ha sido eliminada satisfactoriamente.")
        else:
            bot.reply_to(message, f"No se encontró la acción {stock_symbol} en tus acciones guardadas.")
    except psycopg2.Error as e:
        conn.rollback()
        bot.reply_to(message, f"No se pudo eliminar la acción {stock_symbol}. Error: {e}")
    finally:
        cur.close()
        conn.close()

@bot.message_handler(commands=['portfolio'])
def show_portfolio_info(message):
    # Obtener el ID del usuario
    user_id = message.from_user.id

    # Conectar a la base de datos
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host='db',  # Cambia localhost por el nombre del servicio del contenedor de la base de datos
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    try:
        # Obtener las acciones guardadas del usuario desde la base de datos
        cur.execute("SELECT acciones FROM users WHERE user_id = %s", (user_id,))
        user_actions = cur.fetchone()

        if user_actions and user_actions[0]:
            # Si el usuario tiene acciones guardadas, obtener y enviar información de cada acción
            for stock_symbol in user_actions[0]:
                # Enviar mensaje indicando la acción
                bot.reply_to(message, f"ACCION {stock_symbol}:")
                # Obtener y enviar información de la acción
                enviar_datos_bolsa(message, stock_symbol)
                # Obtener y enviar noticias de la acción
                enviar_noticias(message, stock_symbol)
        else:
            # Si el usuario no tiene acciones guardadas, enviar un mensaje indicándolo
            bot.reply_to(message, "No tienes acciones guardadas en tu portafolio.")
    except psycopg2.Error as e:
        # En caso de error al consultar la base de datos, enviar un mensaje de error
        bot.reply_to(message, f"No se pudo consultar tu portafolio. Error: {e}")
    finally:
        cur.close()
        conn.close()



if __name__ == "__main__":
    bot.polling(none_stop=True)

import telebot
import os
import requests
import json
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('token'))
API_KEY = os.getenv('API_KEY')

# Diccionario para almacenar los símbolos de las acciones proporcionados por los usuarios
acciones = {}

# Comandos
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Soy el bot de Alberto')

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, 'Solo respondo a start y help')

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

    # Construir la URL de la API con el símbolo de la acción
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={stock_symbol}&interval=5min&apikey={API_KEY}'

    # Obtener datos de la API
    response = requests.get(url)

    # Verificar si la solicitud fue exitosa (código de respuesta 200)
    if response.status_code == 200:
        data = json.loads(response.text)
        
        # Filtrar datos para los años 2023 y 2024
        filtered_data = {}
        for date, values in data['Monthly Time Series'].items():
            year = int(date.split('-')[0])
            if year in [2023, 2024]:
                filtered_data[date] = values

        # Crear un mensaje con la información filtrada
        msg = ""
        for date, values in filtered_data.items():
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

        # Invertir el orden de los datos
        dates = dates[::-1]
        close_values = close_values[::-1]

        plt.figure(figsize=(10, 6))
        plt.bar(dates, close_values, color='blue')
        plt.xlabel('Fechas')
        plt.ylabel('Valor de cierre')
        plt.title(f'Valores de cierre de {stock_symbol} en 2023 y 2024')
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

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)

if __name__ == "__main__":
    bot.polling(none_stop=True)


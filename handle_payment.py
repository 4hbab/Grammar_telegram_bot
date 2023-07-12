import os

import requests
from dotenv import load_dotenv
from flask import Flask, request

app = Flask(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


def send_telegram_message(message, chat_id):
    # Send a message to the Telegram bot
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)
    return response.json()


@app.route('/payment/success', methods=['GET'])
def payment_success():
    # Get chat ID from the query parameters
    chat_id = request.args.get('chat_id')
    # Get payment details from the request body
    payment_details = request.json
    # Send a message to the Telegram bot
    send_telegram_message('Payment successful: ' +
                          str(payment_details), chat_id)
    return 'Payment successful', 200


@app.route('/payment/failed', methods=['GET'])
def payment_failed():
    # Get chat ID from the query parameters
    chat_id = request.args.get('chat_id')
    # Get payment details from the request body
    payment_details = request.json
    # Send a message to the Telegram bot
    send_telegram_message('Payment failed: ' + str(payment_details), chat_id)
    return 'Payment failed', 200


@app.route('/payment/cancel', methods=['GET'])
def payment_cancel():
    # Get chat ID from the query parameters
    chat_id = request.args.get('chat_id')
    # Get payment details from the request body
    payment_details = request.json
    # Send a message to the Telegram bot
    send_telegram_message('Payment cancelled: ' +
                          str(payment_details), chat_id)
    return 'Payment cancelled', 200


@app.route('/', methods=['GET'])
def index():
    return 'Payment service'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

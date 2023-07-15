import datetime
import os

import psycopg2
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

app = Flask(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT1_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")


def update_user_paid_status(id):
    # Update the user's paid status in the database
    conn = psycopg2.connect(f"{DATABASE_URL}")
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET paid_status = true WHERE user_id = %s", (id,))
    # Set the subscription date to today's date
    today = datetime.date.now()
    cur.execute(
        "UPDATE users SET subscription_date = %s WHERE user_id = %s", (today, id))
    conn.commit()
    cur.close()
    conn.close()


def send_telegram_message(message, chat_id):
    # Send a message to the Telegram bot
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message['text']
    }
    response = requests.post(url, json=payload)
    return response.json()


@app.route('/payment/success', methods=['POST'])
def payment_success():
    # Get chat ID from the query parameters
    chat_id = request.args.get('chat_id')
    user_id = int(str(chat_id)[-5:])
    # Update paid status of user
    update_user_paid_status(user_id)
    # Get payment details from the request body
    payment_details = request.json
    # Send a message to the Telegram bot
    send_telegram_message(
        {'text': 'Payment successful.\nCongratulations!🥳🐬👌\n\nYou can now use the bot without worrying about payments.', 'payment_details': payment_details}, chat_id)
    return render_template('success.html'), 200


@app.route('/payment/failed', methods=['POST'])
def payment_failed():
    # Get chat ID from the query parameters
    chat_id = request.args.get('chat_id')
    # Get payment details from the request body
    payment_details = request.json
    # Send a message to the Telegram bot
    send_telegram_message(
        {'text': 'Payment failed', 'payment_details': payment_details}, chat_id)
    return render_template('failed.html'), 200


@app.route('/payment/cancel', methods=['POST'])
def payment_cancel():
    # Get chat ID from the query parameters
    chat_id = request.args.get('chat_id')
    # Get payment details from the request body
    payment_details = request.json
    # Send a message to the Telegram bot
    send_telegram_message(
        {'text': 'Payment cancelled', 'payment_details': payment_details}, chat_id)
    return render_template('cancel.html'), 200


@app.route('/', methods=['GET'])
def index():
    return 'Payment service'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

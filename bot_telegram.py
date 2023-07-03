import os
import tempfile

import openai
import speech_recognition as sr
import telebot
from dotenv import load_dotenv
from pydub import AudioSegment
from telebot import types
from telebot.types import Message

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

bot = telebot.TeleBot(BOT_TOKEN)

# These functions use OpenAI API for grammar correction and paraphrasing


def grammar_correction(input_text):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Correct the following text for grammar:\n\n{input_text}",
        temperature=0.5,
        max_tokens=200
    )
    return response.choices[0].text.strip()


def paraphrasing(input_text):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Generate a paraphrase of the following sentence:\n\n{input_text}",
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].text.strip()


def summarizing(input_text):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Summarize the following paragraph:\n\n{input_text}",
        temperature=0.5,
        max_tokens=200
    )
    return response.choices[0].text.strip()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    start_button = types.KeyboardButton('Start')
    markup.add(start_button)

    bot.send_message(
        message.chat.id,
        '🐬Welcome! Press Start to begin.',
        reply_markup=markup
    )


user_states = {}


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    input_text = message.text.lower()

    if message.text.lower() == 'start':
        markup = types.ReplyKeyboardMarkup(row_width=1)
        correction_button = types.KeyboardButton('Correction')
        paraphrase_button = types.KeyboardButton('Paraphrase')
        summary_button = types.KeyboardButton('Summary')
        markup.add(correction_button, paraphrase_button, summary_button)

        bot.send_message(
            message.chat.id,
            'Welcome to the bot! What would you like to do?',
            reply_markup=markup
        )

    elif input_text == "correction":
        bot.reply_to(message, 'Please enter the text you want to correct.')
        user_states[message.chat.id] = 'correction'

    elif input_text == "paraphrase":
        bot.reply_to(
            message, 'Please enter the sentence you want to paraphrase.')
        user_states[message.chat.id] = 'paraphrase'

    elif input_text == "summary":
        bot.reply_to(
            message, 'Please enter the paragraph you want to summarize.')
        user_states[message.chat.id] = 'summary'

    else:
        handle_text(message)


@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_text(message):
    input_text = message.text
    user_state = user_states.get(message.chat.id)

    if user_state == 'correction':
        corrected_text = grammar_correction(input_text)
        bot.reply_to(message, corrected_text)
        user_states[message.chat.id] = None

    elif user_state == 'paraphrase':
        paraphrased_text = paraphrasing(input_text)
        bot.reply_to(message, paraphrased_text)
        user_states[message.chat.id] = None

    elif user_state == 'summary':
        summarized_text = summarizing(input_text)
        bot.reply_to(message, summarized_text)
        user_states[message.chat.id] = None

    else:
        bot.reply_to(
            message, "Please select one of the options by clicking the buttons\n\n or\n\n Start the sentence with the keyword 'Correction', 'Paraphrase' or 'Summary'")


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    # Download the voice message file
    voice_file = bot.get_file(message.voice.file_id)

    # Create a temporary file to save the voice message
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    # Download the voice message file to the temporary location
    downloaded_file = bot.download_file(voice_file.file_path)

    # Save the downloaded file to the temporary location
    with open(file_path, 'wb') as f:
        f.write(downloaded_file)

    # Convert the audio file to the WAV format using pydub
    audio = AudioSegment.from_file(file_path, format="ogg")
    wav_file_path = file_path + ".wav"
    audio.export(wav_file_path, format="wav")

    # Convert the voice file to text using speech_recognition
    r = sr.Recognizer()
    with sr.AudioFile(wav_file_path) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)

    # Pass the text to the existing message handler function
    message.text = text
    echo_all(message)


bot.infinity_polling(timeout=10, long_polling_timeout=5)

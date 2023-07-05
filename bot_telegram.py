import os
import tempfile

import openai
import psycopg2
import speech_recognition as sr
import telebot
from dotenv import load_dotenv
from gtts import gTTS
from pydub import AudioSegment
from telebot import types
from telebot.types import Message

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
openai.api_key = OPENAI_API_KEY

bot = telebot.TeleBot(BOT_TOKEN)

# These functions use OpenAI API for grammar correction, paraphrasing and summarizing


def grammar_correction(input_text):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Generate a grammar correction of the following sentence:\n\n{input_text}",
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

def save_user_data(username, phone_number):
    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(f"{DATABASE_URL}")

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # Execute an SQL query to insert the user data
    query = "INSERT INTO users (username, phone_number) VALUES (%s, %s)"
    values = (username, phone_number)
    cursor.execute(query, values)

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

def save_texts(text):
    conn = psycopg2.connect(f"{DATABASE_URL}")
    cur = conn.cursor()
    if text.startswith("Corrected"):
        updated_text = text.replace("Corrected: ", "")
        cur.execute("UPDATE users SET corrected_texts = array_append(corrected_texts, %s)", (updated_text,))
    elif text.startswith("Paraphrased"):
        updated_text = text.replace("Paraphrased: ", "")
        cur.execute("UPDATE users SET paraphrased_texts = array_append(paraphrased_texts, %s)", (updated_text,))
    elif text.startswith("Summarized"):
        updated_text = text.replace("Summarized: ", "")
        cur.execute("UPDATE users SET summarized_texts = array_append(summarized_texts, %s)", (updated_text,))
    conn.commit()
    cur.close()
    conn.close()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    start_button = types.KeyboardButton('Start')
    # markup.add(start_button)

    bot.send_message(
        message.chat.id,
        "🌟 Drumroll 🌟 Guess who's here to boost your spoken English?\n\nIt's me, Dolphi! Your fantastic language learning buddy!!!!! 🐬 Let's dive into the world of improvement together!",
        reply_markup=markup
    )
    bot.send_message(
        message.chat.id,
        "Alrighty, to get started, I'd love to know your name! 📝 Just type it in, and we'll be friends in no time!"
    )

    bot.register_next_step_handler(message, save_user_data_step)


def save_user_data_step(message):
    # Get the username entered by the user
    username = message.text

    # Create a custom keyboard
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    phone_button = types.KeyboardButton('Share Phone Number', request_contact=True)
    markup.add(phone_button)

    # Ask the user to share their phone number
    bot.send_message(
        message.chat.id, 
        f"Pleasure to meet you, {username}! 🤗 Now, could you kindly share your phone number with me? Don't worry, I won't be calling at odd hours—I'm just eager to help you on your language journey!", 
        reply_markup=markup
    )

    # Register the next step handler to handle the user's response
    bot.register_next_step_handler(message, save_phone_number_step, username)



def save_phone_number_step(message, username):
    # Get the phone number entered by the user
    phone_number = message.contact.phone_number

    # Save the user data to the database
    save_user_data(username, phone_number)

    # Add the keyword buttons
    markup = types.ReplyKeyboardMarkup(row_width=1)
    correction_button = types.KeyboardButton('Correction')
    paraphrase_button = types.KeyboardButton('Paraphrase')
    summary_button = types.KeyboardButton('Summary')
    markup.add(correction_button, paraphrase_button, summary_button)
    # Send a confirmation message to the user
    bot.send_message(message.chat.id, f"Awesome sauce! 🎉 Thanks for sharing, {username}!\n\nNow, let's get to the good stuff. I have three nifty options lined up for you to level up your English skills.\n\nWhich one sparks your interest?\n\n1️⃣ Correction: I'll polish your grammar and fix those sneaky mistakes.\n\n2️⃣ Paraphrase: Want to add some flair to your speech? I'll help you rephrase it in style!\n\n3️⃣ Summarize: Busy day? No problem! Let me condense your text so you can get the gist in a jiffy.\n\n Just let me know which option you're game for, and we'll begin our language adventure! 🚀💬", reply_markup=markup)

    # Reset the user's state
    user_states[message.chat.id] = None

user_states = {}


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    input_text = message.text.lower()

    if input_text == "correction":
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


# @bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_text(message):
    input_text = message.text
    user_state = user_states.get(message.chat.id)

    if user_state == 'correction':
        corrected_text = grammar_correction(input_text)
        formatted_corrected_text = f"Corrected: {corrected_text}"
        tts = gTTS(text=formatted_corrected_text, lang='en')
        tts.save('corrected_text.mp3')
        audio = open('corrected_text.mp3', 'rb')
        bot.send_voice(chat_id=message.chat.id, voice=audio)
        bot.reply_to(message, formatted_corrected_text)
        audio.close()  # Close the file before deleting
        os.remove('corrected_text.mp3')
        save_texts(formatted_corrected_text) 
        user_states[message.chat.id] = None

    elif user_state == 'paraphrase':
        paraphrased_text = paraphrasing(input_text)
        formatted_paraphrased_text = f"Paraphrased: {paraphrased_text}"
        tts = gTTS(text=formatted_paraphrased_text, lang='en')
        tts.save('paraphrased_text.mp3')
        audio = open('paraphrased_text.mp3', 'rb')
        bot.send_voice(chat_id=message.chat.id, voice=audio)
        bot.reply_to(message, formatted_paraphrased_text)
        audio.close()  # Close the file before deleting
        os.remove('paraphrased_text.mp3') 
        save_texts(formatted_paraphrased_text)
        user_states[message.chat.id] = None

    elif user_state == 'summary':
        summarized_text = summarizing(input_text)
        formatted_summarized_text = f"Summarized: {summarized_text}"
        tts = gTTS(text=formatted_summarized_text, lang='en')
        tts.save('summarized_text.mp3')
        audio = open('summarized_text.mp3', 'rb')
        bot.send_voice(chat_id=message.chat.id, voice=audio)
        bot.reply_to(message, formatted_summarized_text)
        audio.close()  # Close the file before deleting
        os.remove('summarized_text.mp3')
        save_texts(formatted_summarized_text)
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

import os
import tempfile

import openai
import speech_recognition as sr
import telebot
from dotenv import load_dotenv
from pydub import AudioSegment

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
        prompt=f"Generate 5 diverse paraphrase of the following sentence:\n\n{input_text}",
        temperature=0.5,
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


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    input_text = message.text
    first_word = input_text.split()[0].lower()

    if first_word == "correction":
        corrected_text = grammar_correction(input_text[11:])
        bot.reply_to(message, corrected_text)

    elif first_word == "paraphrase":
        paraphrased_text = paraphrasing(input_text[11:])
        bot.reply_to(message, paraphrased_text)

    elif first_word == "summary":
        # OpenAI does not directly support text summarization
        # You might need to use a different model or service for this task
        summarized_text = summarizing(input_text[11:])
        bot.reply_to(message, summarized_text)

    else:
        bot.reply_to(
            message, "Please start your message with either 'correction', 'paraphrase' or 'summary'.")


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

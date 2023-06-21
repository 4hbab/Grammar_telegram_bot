import os
import tempfile
import textwrap
from typing import List

import requests
import speech_recognition as sr
from flask import Flask, request
from happytransformer import HappyTextToText, TTSettings
from pydub import AudioSegment
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, T5Tokenizer

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')

app = Flask(__name__)

# Grammar correction
happy_tt = HappyTextToText("T5", "vennify/t5-base-grammar-correction")
tokenizer_gc = T5Tokenizer.from_pretrained(
    "vennify/t5-base-grammar-correction")
args = TTSettings(num_beams=5, min_length=1)

# Paraphrase
device = "cpu"
tokenizer_pp = AutoTokenizer.from_pretrained(
    "humarin/chatgpt_paraphraser_on_T5_base")
model_pp = AutoModelForSeq2SeqLM.from_pretrained(
    "humarin/chatgpt_paraphraser_on_T5_base").to(device)

# Text summarization
happy_tt = HappyTextToText("DISTILBART", "sshleifer/distilbart-cnn-12-6")
top_k_sampling_settings = TTSettings(
    do_sample=True, top_k=50, temperature=0.7, max_length=50)

# This function splits a paragraph into multiple chunks and calls the model with each chunk


def split_text_into_chunks(text: str, max_chunk_size: int = 250) -> List[str]:
    return textwrap.wrap(text, max_chunk_size, break_long_words=True)


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Facebook Messenger verification
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        else:
            return 'Invalid verification token'
    elif request.method == 'POST':
        data = request.json
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if 'message' in messaging_event:
                    sender_id = messaging_event['sender']['id']
                    message = messaging_event['message']

                    if 'text' in message:
                        text = message['text']
                        echo_all(sender_id, text)
                    elif 'attachments' in message:
                        attachments = message['attachments']
                        handle_voice(
                            sender_id, attachments[0]['payload']['url'])

        return 'OK'


def send_message(sender_id, message):
    payload = {
        'recipient': {'id': sender_id},
        'message': {'text': message}
    }
    response = requests.post(
        f'https://graph.facebook.com/v14.0/me/messages?access_token={ACCESS_TOKEN}',
        json=payload
    )
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")


def echo_all(sender_id, input_text):
    first_word = input_text.split()[0].lower()

    def paraphrasing(input_text):
        input_ids = tokenizer_pp(
            f'paraphrase: {input_text}',
            return_tensors="pt", padding="longest",
            max_length=128,
            truncation=True,
        ).input_ids

        outputs = model_pp.generate(
            input_ids, temperature=0.7, repetition_penalty=10.0,
            num_return_sequences=5, no_repeat_ngram_size=2,
            num_beams=5, num_beam_groups=5,
            max_length=128, diversity_penalty=3.0
        )

        return tokenizer_pp.batch_decode(outputs, skip_special_tokens=True)

    if first_word == "correction":
        input_text = f"grammar: {input_text[11:]}"
        text_chunks = split_text_into_chunks(input_text)
        result_texts = []

        for chunk in text_chunks:
            result = happy_tt.generate_text(chunk, args=args)
            result_texts.append(result.text)

        corrected_text = ' '.join(result_texts)
        send_message(sender_id, corrected_text)

    elif first_word == "paraphrase":
        input_text = f"{input_text[11:]}"
        paraphrases = paraphrasing(input_text)
        response_text = f"INPUT TEXT --> {input_text}\n\n"
        for idx, paraphrase in enumerate(paraphrases, start=1):
            response_text += "-" * 50 + "\n\n"
            response_text += f"{idx}. " + paraphrase + "\n\n"
        send_message(sender_id, response_text)

    elif first_word == "summary":
        input_text = f"{input_text[11:]}"
        corrected_text = happy_tt.generate_text(
            input_text, args=top_k_sampling_settings)
        send_message(sender_id, corrected_text.text)
    else:
        send_message(
            sender_id, "Please start your message with either 'correction', 'paraphrase' or 'summary'.")


def handle_voice(sender_id, voice_url):
    # Download the voice message file
    response = requests.get(voice_url)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name

    # Save the downloaded file to the temporary location
    with open(file_path, 'wb') as f:
        f.write(response.content)

    # Convert the audio file to the WAV format using pydub
    audio = AudioSegment.from_file(file_path, format="ogg")
    wav_file_path = file_path + ".wav"
    audio.export(wav_file_path, format="wav")

    # Convert the voice file to text using speech_recognition
    r = sr.Recognizer()
    with sr.AudioFile(wav_file_path) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)

    # Pass the text to the echo_all function
    echo_all(sender_id, text)

    # Clean up the temporary files
    os.remove(file_path)
    os.remove(wav_file_path)


if __name__ == '__main__':
    app.run()

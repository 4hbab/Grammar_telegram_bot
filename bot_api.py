import os
import tempfile
import textwrap
from typing import List

import speech_recognition as sr
from dotenv import load_dotenv
from flask import Flask, request
from happytransformer import HappyTextToText, TTSettings
from pydub import AudioSegment
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, T5Tokenizer
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

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


def echo_all(text):
    input_text = text
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
        return corrected_text

    elif first_word == "paraphrase":
        input_text = f"{input_text[11:]}"
        paraphrases = paraphrasing(input_text)
        response_text = f"INPUT TEXT --> {input_text}\n\n"
        for idx, paraphrase in enumerate(paraphrases, start=1):
            response_text += "-" * 50 + "\n\n"
            response_text += f"{idx}. " + paraphrase + "\n\n"
        return response_text

    elif first_word == "summary":
        input_text = f"{input_text[11:]}"
        corrected_text = happy_tt.generate_text(
            input_text, args=top_k_sampling_settings)
        return corrected_text.text
    else:
        return "Please start your message with either 'correction', 'paraphrase' or 'summary'."


app = Flask(__name__)


@app.route("/bot", methods=["POST"])
def bot():
    input_text = request.form.get("Body")
    response_text = echo_all(input_text)

    # Twilio MessagingResponse object
    resp = MessagingResponse()

    # Added the response text to the MessagingResponse object
    resp.message(response_text)

    # Returned the MessagingResponse object as XML
    return str(resp)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False, port=5000)

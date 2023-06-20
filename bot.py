import os
import textwrap
from typing import List
from happytransformer import HappyTextToText, TTSettings
import telebot
from transformers import T5Tokenizer, AutoTokenizer, AutoModelForSeq2SeqLM

BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

# Grammar correction
happy_tt = HappyTextToText("T5", "vennify/t5-base-grammar-correction")
tokenizer_gc = T5Tokenizer.from_pretrained("vennify/t5-base-grammar-correction")
args = TTSettings(num_beams=5, min_length=1)

# Paraphrase
device = "cpu"
tokenizer_pp = AutoTokenizer.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base")
model_pp = AutoModelForSeq2SeqLM.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base").to(device)

# This function splits a paragraph into multiple chunks and calls the model with each chunk
def split_text_into_chunks(text: str, max_chunk_size: int = 250) -> List[str]:
    return textwrap.wrap(text, max_chunk_size, break_long_words=True)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    input_text = message.text
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
        bot.reply_to(message, corrected_text)

    elif first_word == "paraphrase":
        input_text = f"{input_text[11:]}"
        paraphrases = paraphrasing(input_text)
        response_text = f"INPUT TEXT --> {input_text}\n\n"
        for idx, paraphrase in enumerate(paraphrases, start=1):
            response_text +=  "-" * 50 + "\n\n"
            response_text += f"{idx}. " + paraphrase + "\n\n"
        bot.reply_to(message, response_text)

    else:
        bot.reply_to(message, "Please start your message with either 'correction' or 'paraphrase'.")

bot.infinity_polling(timeout=10, long_polling_timeout = 5)

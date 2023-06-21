# Telegram Grammar Correction and Paraphrase Bot

This is a Telegram bot that performs grammar correcting, paraphrasing or summarizing using the HappyTextToText library and transformers models. It corrects grammar mistakes in text and provides multiple paraphrases for a given input.

## Features

- Grammar correction: The bot can correct grammar mistakes in the provided text using the HappyTextToText library and the T5 model trained for grammar correction.
- Paraphrasing: The bot can generate multiple paraphrases for a given input text using the ChatGPT model fine-tuned for paraphrasing.
- Summarizing: The bot can generate summaries for a given input text using the HappyTextToText library and the T5 model trained for text summarization.

## Setup

1. Clone the repository:

   ```shell
   git clone https://github.com/your-username/telegram-bot.git

   ```

2. Install the necessary dependencies

   ```shell
   pip install -r requirements.txt

   ```

3. Set the BOT_TOKEN

   ```shell
   export BOT_TOKEN=your-bot-token

   ```

4. Run the bot
   ```shell
   python bot.py
   ```

## Usage/Examples

- Start the bot by sending the /start or /hello command. It will respond with a welcome message.

- To correct grammar, send a message starting with the word "correction". For example:

      correction
      Please make sure the all the file are correctly named.

  The bot will correct the grammar in the provided text and reply with the corrected version.

- To get paraphrases, send a message starting with the word "paraphrase". For example:

      paraphrase
      I need some help with my project.

  The bot will generate multiple paraphrases for the input text and reply with the paraphrases.

- To get summarization, send a message starting with the word "summary". For example:

      summary
      The tower is 324 metres (1,063 ft) tall, about the same height as an 81-storey building, and the tallest structure in Paris. Its base is square, measuring 125 metres (410 ft) on each side. During its construction, the Eiffel Tower surpassed the Washington Monument to become the tallest man-made structure in the world, a title it held for 41 years until the Chrysler Building in New York City was finished in 1930. It was the first structure to reach a height of 300 metres. Due to the addition of a broadcasting aerial at the top of the tower in 1957, it is now taller than the Chrysler Building by 5.2 metres (17 ft). Excluding transmitters, the Eiffel Tower is the second tallest free-standing structure in France after the Millau Viaduct.

  The bot will generate multiple paraphrases for the input text and reply with the paraphrases.

- If the message doesn't start with either "correction", "paraphrase" or "summary", the bot will reply with a message asking to start the message with the appropriate keyword.

## License

[BSD-2](https://opensource.org/license/bsd-2-clause/)

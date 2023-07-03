import csv
import json

# Open the input CSV file
with open('eval.csv') as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header row

    # Create a list to store the prompt and completion pairs
    pairs = []

    # Iterate over each row in the CSV file
    for row in reader:
        input_text = row[0].replace("grammar: ", "")
        target_text = row[1]

        # Create a dictionary for the prompt and completion pair
        pair = {
            "prompt": input_text,
            "completion": target_text
        }

        # Add the pair to the list
        pairs.append(pair)

# Export the pairs to a JSON file
with open('pairs1.json', 'w') as f:
    json.dump(pairs, f, indent=4)

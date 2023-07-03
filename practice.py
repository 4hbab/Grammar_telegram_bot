import csv

from datasets import load_dataset

train_dataset = load_dataset("jfleg", split='validation[:]')

eval_dataset = load_dataset("jfleg", split='test[:]')


def generate_csv(csv_path, dataset):
    with open(csv_path, 'w', newline='') as csvfile:
        writter = csv.writer(csvfile)
        writter.writerow(["input", "target"])
        for case in dataset:
            # Adding the task's prefix to input
            input_text = "grammar: " + case["sentence"]
            for correction in case["corrections"]:
                # a few of the cases contain blank strings.
                if input_text and correction:
                    writter.writerow([input_text, correction])


generate_csv("train.csv", train_dataset)
generate_csv("eval.csv", eval_dataset)

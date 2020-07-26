import nltk

try: 
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
import json


def analyze_results(data):
    tokens = nltk.word_tokenize(data[0]['abstract'])
    print(tokens)


if __name__ == "__main__":
    with open('./results.json') as results:
        data = json.loads(results.read())

    analyze_results(data)


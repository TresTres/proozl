import nltk
from nltk.corpus import stopwords

try: 
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
import json



def analyze_results(data):
    result_tokens=[]
    sr = stopwords.words('english')
    for entry in data:
        tokens = nltk.word_tokenize(entry['abstract'])
        clean_tokens = [t for t in tokens if (t.isalnum() and t.lower() not in sr)]
        result_tokens.extend(clean_tokens)

    freq = nltk.FreqDist(result_tokens)
    freq.plot(20, cumulative=False)
    freq_as_dict = dict(freq)
    top_five_after = {w: freq_as_dict[w] for w in sorted(freq_as_dict, key=freq_as_dict.__getitem__, reverse=True)[2:7]}
    print(top_five_after)


if __name__ == "__main__":

    with open('./results.json') as results:
        data = json.loads(results.read())

    analyze_results(data)


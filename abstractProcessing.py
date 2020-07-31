import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from collections import defaultdict

try: 
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

import json


QUERY_WORDS=["black", "hole"]
END_PUNCT=[".!?"]


def analyze_results(data):
    result_tokens=[]
    for entry in data:
        tokens = nltk.word_tokenize(entry['abstract'])
        tokens = pos_tag(tokens)
        result_tokens.extend(tokens)
    
    clean = clean_tokens(result_tokens)
    proper_nouns=clean['proper_nouns']
    terms = clean['terms']
    roots = [root for root, words in terms.items() 
        for w in words]
    pndist = nltk.FreqDist(proper_nouns)
    pn_ten = pndist.most_common(10)
    #print(pn_ten)
    rootdist = nltk.FreqDist(roots)
    root_ten = [(terms[root][0].lower(), freq) for (root, freq) in rootdist.most_common(10)]
    #print(root_ten)
    
    results = {
        'pn10': pn_ten,
        'root10': root_ten
    }

    return results



def clean_tokens(tokens):
    ltzer = WordNetLemmatizer()
    sr = stopwords.words('english')
    clean_tokens = {}
    proper_nouns = []
    terms = defaultdict(lambda: [])
    token_it = iter(tokens)
    for (word, pos) in token_it:
        if word.isalnum() and word.lower() not in sr:

            stem = ltzer.lemmatize(word.lower())
            if stem.lower() not in QUERY_WORDS:
                if pos == 'NNP' or pos == 'NNPS':
                    proper_nouns.append(word)
                else:
                    terms[stem].append(word)
    clean_tokens = {
        'terms': terms,
        'proper_nouns': proper_nouns
    }
    return clean_tokens



if __name__ == "__main__":

    with open('./results.json') as results:
        data = json.loads(results.read())

    rankings = analyze_results(data)
    print(rankings)

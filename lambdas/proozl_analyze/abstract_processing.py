from proozlshared import nltk_setup
import nltk

NLTK_DATA_NEEDS= [
    'corpora/stopwords',
    'coprpora/wordnet',
    'tokenizers/punkt',
    'taggers/averaged_perceptron_tagger'
]
nltk_setup.get_nltk_data(NLTK_DATA_NEEDS)

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from collections import defaultdict

def rank_results(results, query):
    """
    Given a set of Arxiv results which contain paper abstracts and a query,
    finds these rankings using nltk:
    
    1.  The top ten mentioned proper nouns
    2.  The top ten mentioned words that are not part of the original query
    """
    result_tokens = tokenize_abstracts(results);
    clean_toks = clean_tokens(result_tokens, query)

    ranks = {
        'pn10': get_pn10(clean_toks['proper_nouns']),
        'root10': get_rt10(clean_toks['terms'])
    }
    return ranks

def tokenize_abstracts(entries):
    """
    Given a set of entries, tokenizes and assigns tags to all of the words across 
    all of the abstracts 
    """
    result_tokens = []
    for entry in entries:
        tokens = nltk.word_tokenize(entry['summary'])
        tokens = pos_tag(tokens)
        result_tokens.extend(tokens)
    return result_tokens

def clean_tokens(tokens, query):
    """
    Given a list of token words with their parts of speech, creates a dictionary with a structure:
    {
        'terms': A dictionary with the layout:
        {
            stem: A list of the words derived from that stem
        },
        'proper_nouns': A list of proper nouns
    }
    by iterating over each tuple of a word paired with its part of speech and filtering if:
    A. The token is not alphanumeric
    B. The token is not at least 3 characters long
    C. The token is in a list of english stop words
    D. The word stem matches a stem of one of the query words
    """
    #set up
    ltzer = WordNetLemmatizer()
    sr = stopwords.words('english')
    query_stems = [ltzer.lemmatize(qw.lower()) for qw in query.split()]

    proper_nouns = []
    terms = defaultdict(lambda: [])
    clean_tokens = {
        'terms': terms,
        'proper_nouns': proper_nouns
    }

    #iteration
    token_it = iter(tokens)
    for (word, pos) in token_it:
        if word.isalnum() and len(word) > 3 and (word.lower() not in sr):
            stem = ltzer.lemmatize(word.lower())
            if stem.lower() not in query_stems:
                add_clean_token(clean_tokens, word, pos, stem)
    return clean_tokens

def add_clean_token(clean_tokens, word, pos, stem=''):
    """
    Responsible for deciding where in the clean_tokens dictionary a word belongs, 
    based on its part of speech and stem
    """
    
    if pos == 'NNP' or pos == 'NNPS':
        clean_tokens['proper_nouns'].append(word)             
    else:
        clean_tokens['terms'][stem].append(word)       
    return

def get_pn10(proper_nouns):
    """
    Given a list of proper nouns, obtains the top 10 frequently mentioned words
    """
    pndist = nltk.FreqDist(proper_nouns)
    pn10 = [list(tpl) for tpl in pndist.most_common(10)]
    return pn10

def get_rt10(terms):
    """
    Given a collection of words grouped in a dictionary by their stems, obtains
    the top 10 represented words by counting the frequency of stem appearance, using the first word
    for the stem as the representative in the final rank:
    e.g. the top 3 in this dictionary: 
        { 
            "compute": ["computed", "computed", "computing", "computing"],
            "apply": ["apply", "applying", "applying", "applied", "applied"],
            "run": ["ran", "run"],
            "find": ["find", "found", "found", "finds"]
        }
        would yield a result of [["apply", 5], ["compute", 4], ["find", 4]]
    """ 
    roots = [root for root, words in terms.items() 
        for w in words]
    rootdist = nltk.FreqDist(roots)
    rt10 = [list((root.lower(), freq)) for (root, freq) in rootdist.most_common(10)]
    return rt10
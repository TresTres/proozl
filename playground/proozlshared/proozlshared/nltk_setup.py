import nltk
DIR="/tmp"
nltk.data.path.append(DIR)

def get_nltk_data(datalist):
    for entry in datalist:
        try:
            nltk.data.find(entry)
        except LookupError:
            nltk.download(entry.split('/')[-1], download_dir=DIR)
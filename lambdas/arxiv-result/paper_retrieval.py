import requests
import feedparser

API_URL = 'http://export.arxiv.org/api/query'



def extract_abstracts(params):
    response = requests.get(API_URL, params=params,timeout=3)
    if response.status_code != 404:
        results = feedparser.parse(response.content)
        return results
    else:
        return ""   

def process_feed(results=None):
    entries = results.entries
    papers = []
    for entry in entries: 
        paper_entry = {
            "title": entry['title'],
            "link": entry['link'],
            "abstract": entry['summary'],
            "authors": entry['authors']
        }
        papers.append(paper_entry)
    return papers
     
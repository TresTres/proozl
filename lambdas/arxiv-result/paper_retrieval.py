import requests
import feedparser

API_URL = 'http://export.arxiv.org/api/query'



def extract_papers(params):
    """ Queries the Arxiv API using the given paarams and returns the parsed content """
    response = requests.get(API_URL, params=params,timeout=5)
    if response.status_code != 404:
        results = feedparser.parse(response.content)
        return results
    else:
        return ""   

def process_feed(results):
    """ 
    Transforms a feed of papers into a list of json objects with relevant attributes
    of title, link, abstract, and authors
    """
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
     
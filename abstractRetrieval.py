import requests
import feedparser
import json


ARXIV_API_URL="http://export.arxiv.org/api/query?search_query=all:black+hole&start=0&max_results=50"

def extract_abstracts():
    response = requests.get(ARXIV_API_URL, timeout=3)
    if response.status_code != 404:
        results = feedparser.parse(response.content)
        process_feed(results)

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
    with open('results.json', 'w') as outfile:
        json.dump(papers, outfile)
    



if __name__ == "__main__":
    extract_abstracts()
import json
from paper_retrieval import extract_abstracts, process_feed

def lambda_handler(event, context):

    query = event['query']
    params= {
        'search_query': query,
        'start': event['start'],
        'max_results': event['max_results']
    }
    
    data = extract_abstracts(params)
    if not data:
        return {
            'statusCode': 200,
            'body': 'No results found'
        }
    else:
        json_data = process_feed(data)
        return {
            'statusCode': 200,
            'body': json.dumps(json_data)
        }

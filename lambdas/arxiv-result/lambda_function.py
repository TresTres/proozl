import boto3
from boto3.dynamodb.conditions import Key
import uuid
import json
from paper_retrieval import extract_papers, process_feed




def lambda_handler(event, context):

    client = boto3.resource('dynamodb')
    table = client.Table('proozl-arxiv-search-results')

    results = obtain_results(event, table)
    if not results:
        return {
            'statusCode': 200,
            'body': 'No results found'
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }




def obtain_results(event, table):
    """
    Given an event and a table, where the event has the structure:
    {
        'query': The string to search for
        'start': What page # of the paginated results to check
        'max_results': The maximum number of results to show
    }
    1. Checks if the search results are already available in the table for 'query', and imeediately returns the results if they are 
    2. If not, extracts the results using Arxiv API and inserts them in the table before returning
    """
    cached_res = find_in_table(event['query'],table)
    if len(cached_res) == 0:
        #Did not find, fresh search
        return fresh_search(event, table)
    else: 
        #Hit, return results
        return cached_res[0]['results']


def fresh_search(event, table):
    """
    Conducts a fresh search using Arxiv using the params provided in the event
    (see obtain_results):
    1.  Collect the parameters
    2.  Send the parameters to extract_papers, which will grab the papers from Arxiv
    3.  Output is sent to process_feed to turn the search results into a json format
    4.  If the search was successful, insert it into the table before returning.  
        Table entries are structured:
        {
            'query_string': The string searched, which is the primary key
            'page_start': Which page of the results is being examined
            'num_results': Total number of results found (NOT the same as event['max_results'])
            'results': List of results themselves, which are a dict/map (see paper_retrieval.process_feed)
        }
    5.  An unsuccessful search returns an empty string
    """
    
    #Conduct Arxiv search
    query = lower(event['query'])
    start = event['start']
    max_results = event['max_results']
    params= {
        'search_query': query,
        'start': start,
        'max_results': max_results
    }
    json_data = process_feed(extract_papers(params))
    if json_data:
        #Data available, insert into table

        table.put_item(
            Item={
                'query_string': query,
                'page_start': start,
                'num_results': len(json_data), 
                'results': json_data
            }
        )
        return json_data
    #Otherwise return nothing
    return ''

def find_in_table(query, table):
    """Searches the table for the query_string that matches query"""
    """Warning: does not take pagination into account yet"""
    result = table.query(KeyConditionExpression=Key('query_string').eq(lower(query)))
    return result['Items']
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import uuid
import json
from proozlshared.paper_retrieval import extract_papers, process_feed




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
    1. Checks if the search results are already available in the table for 'query' and 'start'
            If results are found, the number of hits is updated and the results are returned.  
            If not, extracts the results using Arxiv API and inserts them in the table before returning
    """
    query = event['query']
    start = event['start']

    cached = find_in_table(query, start, table)
    if not cached or cached['Count'] == 0:
        #Did not find, fresh search
        return fresh_search(event, table)
    else: 
        #Hit, return results
        content = cached['Items'][0]
        id = content['id']
        results = content['results']
        update_hits(id, table)
        return results

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
            'num_of_hits_wk': Number of times the search has been conducted this week
            'num_of_hits_all': Number of times the search has happened across all time
            'results': List of results themselves, which are a dict/map (see paper_retrieval.process_feed)
        }
    5.  An unsuccessful search returns an empty string
    """
    
    #Conduct Arxiv search
    query = event['query'].lower()
    start = event['start']
    max_results = 60
    params = {
        'search_query': query,
        'start': start,
        'max_results': max_results,
        'sortBy': 'lastUpdatedDate'
    }
    

    json_data = process_feed(extract_papers(params))
    if json_data:
        #Data available, insert into table

        table.put_item(
            Item={
                'id': json_data['id'],
                'query_string': query,
                'page_start': start,
                'num_results': len(json_data['results']), 
                'num_of_hits_wk': 1,
                'num_of_hits_all': 1,
                'results': json_data['results']
            }
        )
        return json_data['results']
    #Otherwise return nothing
    return ''


def update_hits(id, table):
    """
    Updates the table using the id primary index to increase
    [num_of_hits_wk, num_of_hits_all] by 1
    """
    try:
        table.update_item(
            Key={'id': id},
            UpdateExpression="set \
                num_of_hits_wk = num_of_hits_wk + :val, \
                num_of_hits_all = num_of_hits_all + :val",
            ExpressionAttributeValues={
                ':val': 1
            },
            ReturnValues="NONE"
        )
    except ClientError as e: 
        print(e.response['Error']['Message'])


def find_in_table(query, start, table):
    """Searches the table for the query_string that matches query and page_start"""
    try: 
        result = table.query(
            IndexName="query_string",
            KeyConditionExpression="query_string = :query_val \
                AND page_start = :start_val",
            ExpressionAttributeValues={
                ':query_val': query.lower(),
                ':start_val': start
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return result




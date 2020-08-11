import boto3
import json
from boto3.dynamodb.conditions import Key
from lambdas.proozl_analyze.abstract_processing import rank_results


DYNAMO_METHODS=["INSERT", "UPDATE"]
GATEWAY_METHODS=["REQUEST"]

def lambda_handler(event, context):

    client = boto3.resource('dynamodb')
    results_table = client.Table('proozl-arxiv-search-results')
    analysis_table = client.Table('proozl-result-analyses')

    method = get_event_method(event)

    if method in DYNAMO_METHODS:
        for record in event["Records"]:
            query = extract_query(record)
            analysis = analyze_results(query, results_table)
            if not analysis:
                return {
                    'statusCode': 200,
                    'body': 'No results found.'
                }
            else:
                insert_analysis(query, analysis, analysis_table)
                return {
                    'statusCode': 200,
                    'body': json.dumps(analysis)
                }
    if method in GATEWAY_METHODS:
        query = event['query']
        analysis = analyze_results(query, results_table)
        if not analysis:
            return {
                'statusCode': 200,
                'body': 'No results found.'
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps(analysis)
            }



def get_event_method(event):
    '''
    Given an event, determines the event type.  Events can come from:
    -DynamoDB stream
    -Request to API Gateway
    If the event comes from a DynamoDB stream, the event name is returned.
    '''
    if 'Records' in event:
        return event['Records'][0]['eventName']
    else:
        return 'REQUEST'


def extract_query(record):
    '''
    Given a record from a Dynamo stream that updates the arxiv-result table, 
    extracts the query_string query
    '''
    if 'dynamodb' in record:
        keys = record['dynamodb']['Keys']
        if keys['query_string']:
            return keys['query_string']['S']
    else:
        return ''

def analyze_results(query, table):
    '''
    Given a query and a table containing query strings matched to a list of 
    Arxiv search results, conducts analyses on the results that correspond to the query

    If no results are in the table that match the query, nothing is returned.
    Otherwise, the following analyes are done:
        -Word ranking data pulled from the abstracts
        -...
    '''
    analysis = {}
    results = obtain_results(query, table)
    if results:
        analysis = {
            'word_rankings': rank_results(results, query)
        }
    return analysis



def insert_analysis(query, analysis, table):
    '''
    Given a query, an analysis dictionary, and a table that maps queries to analyses, 
    inserts the analysis into the table for the query if an entry does not yet exist.
    '''
    table.put_item(
        Item={
            'query_string': query,
            'analysis': analysis
        }
    )
    return

def obtain_results(query, table):
    """
    Given a query and a table, where the event has the structure:
    1. Checks if the search results are already available in the table for query, and imeediately returns the results if they are 
    2. If not, returns nothing
    """
    cached_res = find_in_table(query, table)
    if len(cached_res) == 0:
        #Did not find, return nothing
        return ''
    else: 
        #Hit, return results
        return cached_res[0]['results']

def find_in_table(query, table):
    """Searches the table for the query_string that matches query"""
    """Warning: does not take pagination into account yet"""
    result = table.query(KeyConditionExpression=Key('query_string').eq(query.lower()))
    return result['Items']
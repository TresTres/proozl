import boto3
from boto3.dynamodb.conditions import Key
from abstract_processing import rank_results

TABLE_INSERT="TABLE_INSERT"


def lambda_handler(event, context):

    client = boto3.resource('dynamodb')
    results_table = client.Table('proozl-arxiv-search-results')
    analysis_table = client.Table('proozl-result-analyses')

    if event['method'] == TABLE_INSERT:
        query = event['query']
        analysis = analyze_results(event, results_table)
        insert_analysis(query, analysis, analysis_table)
        return {
            'statusCode': 200,
            'body': analysis
        }


def analyze_results(event, table):
    '''
    Given an event and a table containing query strings matched to a list of 
    Arxiv search results, conducts analyses on the results that correspond to event['query']

    If no results are in the table that match the query, nothing is returned.
    Otherwise, the following analyes are done:
        -Word ranking data pulled from the abstracts
        -...
    '''
    analysis = {}
    query = event['query']
    results = obtain_results(event, table)
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
    return

def obtain_results(event, table):
    """
    Given an event and a table, where the event has the structure:
    {
        'query': The string to search for
    }
    1. Checks if the search results are already available in the table for 'query', and imeediately returns the results if they are 
    2. If not, returns nothing
    """
    cached_res = find_in_table(event['query'], table)
    if len(cached_res) == 0:
        #Did not find, return nothing
        return ''
    else: 
        #Hit, return results
        return cached_res[0]['results']

def find_in_table(query, table):
    """Searches the table for the query_string that matches query"""
    """Warning: does not take pagination into account yet"""
    result = table.query(KeyConditionExpression=Key('query_string').eq(query))
    return result['Items']
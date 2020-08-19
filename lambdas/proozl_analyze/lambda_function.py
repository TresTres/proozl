import boto3
import json
import decimal
import uuid
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from lambdas.proozl_analyze.abstract_processing import rank_results

class DecimalIntEncoder(json.JSONEncoder):
    '''Need custom encoder because DynamoDB stores numbers as Decimals'''
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super(DecimalIntEncoder, self).default(o)



DYNAMO_METHODS=["INSERT", "UPDATE"]
GATEWAY_METHODS=["REQUEST"]

def lambda_handler(event, context):

    client = boto3.resource('dynamodb')
    results_table = client.Table('proozl-arxiv-search-results')
    analysis_table = client.Table('proozl-result-analyses')

    method = get_event_method(event)

    if method in DYNAMO_METHODS:
        return dynamo_handler(event['Records'], results_table, analysis_table)
 
    if method in GATEWAY_METHODS:
        return request_handler(event, analysis_table)


def dynamo_handler(records, results_table, analysis_table):
    '''
    If this handler is called, that means there's new info in the results table
    1. For the (assumed) sole record in records, the relevant info is extracted
    2. Analysis is then conducted using the info and the results table
    3. If the analysis is successful: 
            The analyses table is checked.
            If the info is stored in the table:
                The table is updated
            Otherwise, it's inserted into the table
            A response containing the analysis results is prepared
        Otherwise, an empty response is prepared
    '''
    record = records[0]
    info = extract_info(record)
    analysis = analyze_results(info, results_table)
    if not analysis:
        return {
            'statusCode': 200,
            'body': 'No results found.'
        }
    else:
        old_id = obtain_items(info, analysis_table, 'id')
        if old_id:
            update_analysis(old_id, analysis, analysis_table)
        else:
            insert_analysis(info, analysis, analysis_table)
        return {
            'statusCode': 200,
            'body': json.dumps(analysis)
        }

def request_handler(event, analysis_table):
    '''
    This handler queries the analysis table for analyses
    that correspond to the info in the event:
    {
        query: <some string>
        start: <some number>
    }
    If the analyses exist, they are prepared in a response.
    Otherwise, an empty resopnse is prepared.
    '''
    analysis = obtain_items(event, analysis_table, 'analysis')
    if not analysis:
        return {
            'statusCode': 200,
            'body': 'No results found.'
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps(analysis, cls=DecimalIntEncoder)
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


def extract_info(record):
    '''
    Given a record from a Dynamo stream that updates the arxiv-result table, 
    extracts the query_string and page_start
    '''
    if 'dynamodb' in record:
        image = record['dynamodb']['NewImage']
        return {
            'query': image['query_string']['S'],
            'start': int(image['page_start']['N'])
        }
            
    else:
        return {}



def analyze_results(spec, results_table):
    '''
    Given a spec that contains a query and start item, and a table containing 
    query strings matched to a list of Arxiv search results, conducts analyses 
    on the results that correspond to the spec['query'] and spec['start']

    If no results are in the table that match the query, nothing is returned.
    Otherwise, the following analyses are done:
        -Word ranking data pulled from the abstracts
        -...
    '''
    analysis = {}
    query = spec['query'].lower()
    results = obtain_items(spec, results_table, 'results')
    if results:
        analysis = {
            'word_rankings': rank_results(results, query)
        }
    return analysis

def update_analysis(old_id, analysis, analysis_table):
    '''
    Updates an item with the old_id inside the analysis table
    with the contents of analysis
    '''
    try:
        analysis_table.update_item(
            Key={'id': id},
            UpdateExpression="set \
                analysis = :new_analysis",
            ExpressionAttributeValues={
                ':new_analysis': analysis
            },
            ReturnValues="NONE"
        )
    except ClientError as e: 
        print(e.response['Error']['Message'])


def insert_analysis(spec, analysis, analysis_table):
    '''
    Given a spec with a query and start, an analysis dictionary, and a table that 
    maps queries to analyses, inserts the analysis into the table for the 
    query/start combo if an entry does not yet exist.
    '''
    analysis_table.put_item(
        Item={
            'id': str(uuid.uuid4()),
            'query_string': spec['query'].lower(),
            'page_start': spec['start'],
            'analysis': analysis
        }
    )
    return

def obtain_items(spec, table, key):
    """
    Given an spec, a table, and a key string where the spec has the structure:
    {
        query: <some string>,
        start: <some number>
    }
    1. Checks if an item according to spec exists in the table, and if it does, returns 
        the info specified by the key
    2. If not, returns nothing
    """
    query = spec['query']
    start = spec['start']

    cached = find_in_table(query, start, table)
    if not cached or cached['Count'] == 0:
        #Did not find, return nothing
        return {}
    else: 
        #Hit, return results
        return cached['Items'][0][key]

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




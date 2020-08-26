import boto3
from boto3.dynamodb.conditions import Key
import time
from proozlshared.paper_retrieval import extract_papers, process_feed

def lambda_handler(event, context):

    client = boto3.resource('dynamodb')
    table = client.Table('proozl-arxiv-search-results')

    update_results(table)
    

def update_results(table):
    '''
    Loops through each item in the table and updates it with a new search
    using the parameters in the item
    '''
    results = table.scan()
    max_results = 60
    update_count = 0
    clear_count = 0
    while True:
        for item in results['Items']:
            params = {
            'search_query': item['query_string'],
            'start': item['page_start'],
            'max_results': max_results,
            'sortBy': 'lastUpdatedDate'
            }

            json_data = process_feed(extract_papers(params))
            time.sleep(3)
            if json_data:
                update_item(table, item['id'], json_data)
                update_count += 1
            else: 
                clear_item(table, item['id'])
                clear_count += 1
        if 'LastEvaluatedKey' not in results:
            break
        else:
            results = table.scan(ExclusiveStartKey = results['LastEvaluatedKey'])
    print('Updated: {0}, Cleared: {1}'.format(update_count, clear_count))
    

def update_item(table, id, json_data):

    table.update_item(
        Key={'id': id},
        UpdateExpression="set \
            num_results = :num_results, \
            results = :new_results",
        ExpressionAttributeValues={
            ':num_results': len(json_data['results']),
            ':new_results': json_data['results']
        },
        ReturnValues="NONE"
    )

def clear_item(table, id):
    
    table.update_item(
        Key={'id': id},
        UpdateExpression="set \
            num_results = :num_results, \
            results = :new_results",
        ExpressionAttributeValues={
            ':num_results': 0,
            ':new_results': []
        },
        ReturnValues="NONE"
    )
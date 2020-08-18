import boto3
from boto3.dynamodb.conditions import Key
import uuid

def lambda_handler(event, context):

    client = boto3.resource('dynamodb')
    table = client.Table('proozl-arxiv-search-results')


    update_results(table)
    print('Scan complete')

def update_results(table):
    '''
    Loops through each item in the table and updates it with a new search
    using the parameters in the item
    '''
    results = table.scan()
    print(results)

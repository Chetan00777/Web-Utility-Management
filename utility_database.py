import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')  # Connect to DynamoDB using default AWS credentials
TABLE_NAME = 'UtilityRecords2025'       # Our DynamoDB table for storing all utility records

def create_utility_table():
    # Creates a table for utility records if it doesn't already exist
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{'AttributeName': 'utility_id', 'KeyType': 'HASH'}],  # Each record is uniquely identified by its utility_id
            AttributeDefinitions=[{'AttributeName': 'utility_id', 'AttributeType': 'S'}],  # Declares utility_id as a string
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}  # Low capacity for demo usage
        )
        table.wait_until_exists()  # Pause until AWS confirms our table is ready
        print(f"Table '{TABLE_NAME}' created in us-east-1.")
    except ClientError as e:
        print(f"Table creation error: {e}")  # Helpful feedback if AWS blocks the table creation

def build_util_id(pk):
    return f'util-{pk}'  # Build a unique ID string using the record's primary key

def add_utility_record(pk, utype, usage, date, notes):
    table = dynamodb.Table(TABLE_NAME)
    util_id = build_util_id(pk)
    table.put_item(Item={
        'utility_id': util_id,        # Unique string for this record
        'type': utype,                # Utility type (e.g., electricity, gas)
        'usage': usage,               # How much was used (float or int)
        'date': date,                 # When this usage entry was made
        'notes': notes                # Any extra info the user added
    })
    print(f"Record {util_id} added.")

def get_utility_record(pk):
    table = dynamodb.Table(TABLE_NAME)
    util_id = build_util_id(pk)
    # Fetch a single record by primary key (returns None if not found)
    item = table.get_item(Key={'utility_id': util_id}).get('Item')
    print(f"Fetched: {item}")
    return item

def update_utility_record(pk, updates):
    table = dynamodb.Table(TABLE_NAME)
    util_id = build_util_id(pk)
    # Only updates the 'usage' field—change as needed for more fields
    table.update_item(
        Key={'utility_id': util_id},
        UpdateExpression="SET usage = :u",
        ExpressionAttributeValues={':u': updates['usage']}  # expects a single value for 'usage'
    )
    print(f"Record {util_id} updated.")

def delete_utility_record(pk):
    table = dynamodb.Table(TABLE_NAME)
    util_id = build_util_id(pk)
    table.delete_item(Key={'utility_id': util_id})  # Permanently removes the entry (danger: no undo)
    print(f"Record {util_id} deleted.")

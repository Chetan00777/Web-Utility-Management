import boto3

# Connect to DynamoDB in our usual AWS region (us-east-1)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_file_uploads_table():
    # This function will create a DynamoDB table called 'UtilityFileUploads2025'.
    try:
        table = dynamodb.create_table(
            TableName='UtilityFileUploads2025',  # Table for logging every file uploaded to S3
            KeySchema=[
                {'AttributeName': 'file_key', 'KeyType': 'HASH'}  # Use file_key as unique identifier for each file
            ],
            AttributeDefinitions=[
                {'AttributeName': 'file_key', 'AttributeType': 'S'}  # file_key will always be a string for us
            ],
            BillingMode='PAY_PER_REQUEST'  # No need to pre-provision capacity, just pay for our actual usage
        )
        table.wait_until_exists()  # Don't move forward until AWS confirms the table is active
        print("Table 'UtilityFileUploads2025' created successfully!")  # Friendly success message for setup confirmation
        print(f"Status: {table.table_status}")  # This shows either ACTIVE (ready to use) or what AWS is still doing
    except Exception as e:
        print(f"Error creating table: {e}")  # If something fails (already existing, or network issue), show what happened

if __name__ == '__main__':
    create_file_uploads_table()  # If we call this script directly, go and create the DynamoDB table for our app log

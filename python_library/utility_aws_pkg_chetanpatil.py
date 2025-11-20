import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Core AWS utility class for S3, DynamoDB, SQS, SNS
class UtilityAWS:
    def __init__(self, region='us-east-1'):
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sqs = boto3.client('sqs', region_name=region)
        self.sns = boto3.client('sns', region_name=region)

    # S3 Methods
    def upload_file_to_s3(self, bucket_name, local_path, remote_key):
        try:
            self.s3.upload_file(local_path, bucket_name, remote_key)
            print(f"Uploaded {local_path} to S3 as {remote_key}")
            return True
        except ClientError as e:
            print(f"S3 upload error: {e}")
            return False

    def list_s3_files(self, bucket_name, prefix=''):
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            print(f"S3 list error: {e}")
            return []

    # DynamoDB Methods
    def add_utility_record(self, table_name, utility_id, utility_type, usage, date, notes=''):
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item={
                'utility_id': str(utility_id),
                'type': utility_type,
                'usage': str(usage),
                'date': date,
                'notes': notes
            })
            print(f"Added record {utility_id} to {table_name}")
            return True
        except ClientError as e:
            print(f"DynamoDB add error: {e}")
            return False

    def get_utility_record(self, table_name, utility_id):
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key={'utility_id': str(utility_id)})
            return response.get('Item', None)
        except ClientError as e:
            print(f"DynamoDB get error: {e}")
            return None

    def delete_utility_record(self, table_name, utility_id):
        try:
            table = self.dynamodb.Table(table_name)
            table.delete_item(Key={'utility_id': str(utility_id)})
            print(f"Deleted record {utility_id} from {table_name}")
            return True
        except ClientError as e:
            print(f"DynamoDB delete error: {e}")
            return False

    # SQS Methods
    def send_sqs_message(self, queue_name, message_body):
        try:
            response = self.sqs.get_queue_url(QueueName=queue_name)
            queue_url = response['QueueUrl']
            self.sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
            print(f"Sent message to {queue_name}")
            return True
        except ClientError as e:
            print(f"SQS send error: {e}")
            return False

    # SNS Methods
    def publish_sns_notification(self, topic_arn, message, subject='Notification'):
        try:
            self.sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
            print(f"Notification sent: {subject}")
            return True
        except ClientError as e:
            print(f"SNS publish error: {e}")
            return False

# --- GLOBAL INTEGRATION WRAPPERS FOR DJANGO IMPORTS ---

aws = UtilityAWS(region='us-east-1')
BUCKET_NAME = 'utility-management-files-2025'
TABLE_NAME = 'UtilityRecords2025'
QUEUE_NAME = 'utility-tasks-queue-2025'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:263072075949:utility-alerts-topic-2025'

def upload_utility_file(local_path, remote_key):
    return aws.upload_file_to_s3(BUCKET_NAME, local_path, remote_key)

def add_utility_record(utility_id, utility_type, usage, date, notes=''):
    return aws.add_utility_record(TABLE_NAME, utility_id, utility_type, usage, date, notes)

def delete_utility_record(utility_id):
    return aws.delete_utility_record(TABLE_NAME, utility_id)

def send_utility_task(queue_url_or_name, message_body):
    return aws.send_sqs_message(queue_url_or_name, message_body)

def create_utility_queue():
    return QUEUE_NAME

def publish_utility_alert(topic_arn, message, subject='Utility Alert'):
    return aws.publish_sns_notification(topic_arn, message, subject)

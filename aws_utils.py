# Custom aws integeration for AWS S3, DynamoDB, SNS and SQS
from utility_aws_pkg import UtilityAWS
from decimal import Decimal

aws = UtilityAWS(region='us-east-1')
BUCKET_NAME = 'utility-management-files-2025'
TABLE_NAME = 'UtilityRecords2025'
QUEUE_NAME = 'utility-tasks-queue-2025'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:263072075949:utility-alerts-topic-2025'

def upload_utility_file(local_path, remote_key):
    return aws.upload_file_to_s3(BUCKET_NAME, local_path, remote_key)

def list_utility_files(prefix=''):
    return aws.list_s3_files(BUCKET_NAME, prefix)

def add_utility_record(utility_id, utility_type, usage, date, notes=''):
    return aws.add_utility_record(TABLE_NAME, utility_id, utility_type, usage, date, notes)

def get_utility_record(utility_id):
    return aws.get_utility_record(TABLE_NAME, utility_id)

def delete_utility_record(utility_id):
    return aws.delete_utility_record(TABLE_NAME, utility_id)

def send_utility_task(queue_url_or_name, message_body):
    # function accepts: queue URL or queue name
    # aws.send_sqs_message handles both
    return aws.send_sqs_message(queue_url_or_name, message_body)

def create_utility_queue():
    # returns the queue name (not URL)
    return QUEUE_NAME

def publish_utility_alert(topic_arn, message, subject='Utility Alert'):
    return aws.publish_sns_notification(topic_arn, message, subject)

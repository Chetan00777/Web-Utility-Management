import json
import boto3
from urllib.parse import unquote_plus
from datetime import datetime

s3 = boto3.client('s3')  # S3 client for file metadata checks
sns = boto3.client('sns')  # SNS client to send system notifications
dynamodb = boto3.resource('dynamodb')  # DynamoDB for log storage

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:263072075949:utility-alerts-topic-2025'  # Our SNS topic ARN

def lambda_handler(event, context):
    print(f"Lambda triggered with event: {json.dumps(event)}")
    processed_files = []  # List to capture all processed file keys

    # Check if triggered programmatically (e.g., via Django app, not just S3 event)
    if 'bucket' in event and 'key' in event:
        bucket = event['bucket']
        key = event['key']
        if key:
            key = unquote_plus(key)  # Handles URL-encoded S3 keys
        print(f"Processing file (direct trigger): s3://{bucket}/{key}")
        try:
            file_metadata = s3.head_object(Bucket=bucket, Key=key)  # Look up details for file
            file_size = file_metadata['ContentLength']
            file_type = file_metadata.get('ContentType', 'unknown')
            print(f"File size: {file_size} bytes")
            print(f"File type: {file_type}")
            utility_type = determine_utility_type(key)  # Guess utility based on filename
            print(f"Detected utility type: {utility_type}")
            send_file_notification(bucket, key, file_size, file_type, utility_type)  # Alert via SNS
            log_file_upload(bucket, key, file_size, file_type, utility_type)  # Store info in DynamoDB table
            processed_files.append(key)
        except Exception as e:
            print(f"Error processing file {key}: {str(e)}")

    # If triggered by an S3 upload event, loop through all records
    elif 'Records' in event:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            print(f"Processing file (S3 event): s3://{bucket}/{key}")
            try:
                file_metadata = s3.head_object(Bucket=bucket, Key=key)
                file_size = file_metadata['ContentLength']
                file_type = file_metadata.get('ContentType', 'unknown')
                print(f"File size: {file_size} bytes")
                print(f"File type: {file_type}")
                utility_type = determine_utility_type(key)
                print(f"Detected utility type: {utility_type}")
                send_file_notification(bucket, key, file_size, file_type, utility_type)
                log_file_upload(bucket, key, file_size, file_type, utility_type)
                processed_files.append(key)
            except Exception as e:
                print(f"Error processing file {key}: {str(e)}")
                continue
    else:
        print("Unsupported event format.")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Files processed successfully',
            'processed_files': processed_files,
            'count': len(processed_files)
        })
    }

def determine_utility_type(filename):
    # Try to guess type of utility by looking for keywords in the filename or S3 path
    filename_lower = filename.lower()
    if '/electricity/' in filename_lower:
        return 'electricity'
    elif '/gas/' in filename_lower:
        return 'gas'
    elif '/steam/' in filename_lower:
        return 'steam'
    elif '/air_conditioning/' in filename_lower:
        return 'air_conditioning'
    if 'electricity' in filename_lower or 'electric' in filename_lower:
        return 'electricity'
    elif 'gas' in filename_lower:
        return 'gas'
    elif 'steam' in filename_lower:
        return 'steam'
    elif 'air' in filename_lower or 'ac' in filename_lower or 'conditioning' in filename_lower:
        return 'air_conditioning'
    return 'unknown'

def send_file_notification(bucket, key, size, file_type, utility_type):
    # Compose and deliver a notification about a new file using SNS
    try:
        size_kb = round(size / 1024, 2)
        utility_display = utility_type.replace('_', ' ').title()
        subject = f"New Utility File Uploaded - {utility_display}"
        message = (
            f"NEW UTILITY FILE UPLOADED\n"
            f"File Name: {key}\n"
            f"Utility Type: {utility_display}\n"
            f"File Size: {size_kb} KB\n"
            f"File Type: {file_type}\n"
            f"S3 Location: s3://{bucket}/{key}\n"
            f"The file has been successfully stored and is ready for processing.\n"
            f"Utility Management System\n"
            f"Automated notification from AWS Lambda"
        )
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"Notification sent for {key}")
        return True
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False

def log_file_upload(bucket, key, size, file_type, utility_type):
    # Store details about the new upload in our DynamoDB table for tracking/reporting
    try:
        table = dynamodb.Table('UtilityFileUploads2025')
        table.put_item(Item={
            'file_key': key,
            'bucket': bucket,
            'file_size': size,
            'file_type': file_type,
            'utility_type': utility_type,
            'upload_timestamp': datetime.now().isoformat(),
            'status': 'uploaded',
            'processed': False
        })
        print(f"Upload logged to DynamoDB")
        return True
    except Exception as e:
        print(f"Could not log to DynamoDB: {str(e)}")
        return False

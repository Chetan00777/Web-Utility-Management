# SQS basic utility functions for queued task processing in my Utility Management System.
# These functions use boto3 to interact with Amazon Simple Queue Service (SQS).

import boto3

sqs = boto3.client('sqs')  # Connect to AWS SQS using your current credentials
QUEUE_NAME = 'utility-tasks-queue-2025'  # This is the name of the queue we'll use for all app tasks

def create_utility_queue():
    # Create the SQS queue. If it already exists, AWS just returns its info.
    url = sqs.create_queue(QueueName=QUEUE_NAME)['QueueUrl']  # Get URL (unique address) for queue operations
    print(f"Queue URL: {url}")  # Print it for fast reference or troubleshooting
    return url

def send_utility_task(queue_url, message):
    # Add a new message (task) to the SQS queue for later processing
    sqs.send_message(QueueUrl=queue_url, MessageBody=message)  # SQS will store this for worker/Lambda pickup
    print(f"Sent: {message}")  # Confirm success so users/devs know it worked

def receive_utility_task(queue_url):
    # Pull one message from the queue (if present) for processing
    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    for msg in messages.get('Messages', []):  # There might be 0 or more messages
        print("Received:", msg['Body'])  # Show the message content
        # This is where you would handle the message logic in a real app
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg['ReceiptHandle'])  # Remove from queue after handling

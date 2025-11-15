# SNS basic utility functions for managing alerts in my Utility Management System.
# These functions use boto3 to interact with AWS Simple Notification Service.

import boto3

sns = boto3.client('sns')  # Connect to AWS SNS using your credentials/config
TOPIC_NAME = 'utility-alerts-topic-2025'  # This topic will deliver utility alerts to subscribers

def create_utility_topic():
    # Create the SNS topic (does nothing if it already exists)
    topic_arn = sns.create_topic(Name=TOPIC_NAME)['TopicArn']  # ARN is SNS's unique identifier for the topic
    print(f"Topic ARN: {topic_arn}")  # Useful for reference in other functions or manual checks
    return topic_arn

def publish_utility_alert(topic_arn, message):
    # Publish (send) a notification to everyone who subscribes to this topic
    sns.publish(TopicArn=topic_arn, Message=message)  # Delivers 'message' to all configured endpoints (email, SMS, etc)
    print(f"Alert sent: {message}")

def subscribe_to_utility_alert(topic_arn, protocol, endpoint):
    # Add a new subscriber (email, SMS, or lambda, etc) to the topic
    sns.subscribe(TopicArn=topic_arn, Protocol=protocol, Endpoint=endpoint)
    print(f"Subscribed {endpoint} to {topic_arn}.")  # Confirm action for debugging or user info

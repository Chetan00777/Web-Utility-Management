# AWS S3 utility functions for cloud file management in my Utility Management System project.
# All actions use boto3 (the official AWS Python SDK) to connect, store, fetch, and remove utility files.

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')  # This gives us the S3 connection, using current environment's credentials
BUCKET_NAME = 'utility-management-files-2025'  # All utility app files go in this S3 bucket

def create_utility_bucket():
    # Try to create the bucket (does nothing if it already exists)
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)  # S3 buckets must be globally unique
        print("Bucket created in us-east-1.")  # Always double-check region matches your config!
    except ClientError as e:
        print(f"Bucket creation error: {e}")  # Details if the bucket exists or AWS blocks the request

def upload_utility_file(local_path, remote_key, utility_type='unknown'):
    # Upload a file (at local_path) to S3 at remote_key, add utility type as metadata for indexing/search
    try:
        s3.upload_file(
            local_path, BUCKET_NAME, remote_key,
            ExtraArgs={'Metadata': {'utility-type': utility_type}}
        )
        print(f"Uploaded '{local_path}' as '{remote_key}' with type '{utility_type}'.")
    except ClientError as e:
        print(f"Upload error: {e}")  # See AWS permission or bucket errors here

def list_utility_files():
    # List all files in our S3 bucket (useful for dashboards or file admin pages)
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME)  # Pulls metadata on every object in the bucket
        files = [obj['Key'] for obj in resp.get('Contents', [])]  # Only needs the file 'Key' names
        print(f"Files: {files}")
        return files
    except ClientError as e:
        print(f"List files error: {e}")

def download_utility_file(remote_key, local_path):
    # Copy a file from S3 down to the user's or server's local directory
    try:
        s3.download_file(BUCKET_NAME, remote_key, local_path)
        print(f"Downloaded '{remote_key}' to '{local_path}'.")
    except ClientError as e:
        print(f"Download error: {e}")

def remove_utility_file(remote_key):
    # Permanently delete a file from S3 (be careful, no undo unless versioning is on)
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=remote_key)
        print(f"Deleted '{remote_key}'.")
    except ClientError as e:
        print(f"Delete error: {e}")

if __name__ == "__main__":
    create_utility_bucket()  # Easy way to make sure the bucket is ready for uploads, only runs if script called directly

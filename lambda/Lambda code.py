import json
import boto3
import os
import uuid
from urllib.parse import unquote_plus
from botocore.config import Config

s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))

def lambda_handler(event, context):
    """
    Placeholder S3 Trigger Lambda
    Since image resizing is now handled efficiently on the Client-Side (Frontend Browser),
    this Lambda no longer needs Pillow or any Layers.
    
    It simply logs the incoming S3 events. You can use it to store metadata in DynamoDB 
    if you want to track uploads in the future.
    """
    try:
        # Get the bucket and key from the S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = unquote_plus(event['Records'][0]['s3']['object']['key'])
        
        print(f"File uploaded successfully to S3: {bucket}/{key}")
        
        # Extract job ID from the key if it matches uploads/{job_id}/{filename}
        key_parts = key.split('/')
        if len(key_parts) >= 3:
            job_id = key_parts[1]
        else:
            job_id = str(uuid.uuid4())
            
        print(f"Associated Job ID: {job_id}")

        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'jobId': job_id,
                'fileKey': key,
                'message': 'File tracked successfully (Processing handled by Client-Side)'
            })
        }
        
    except Exception as e:
        print(f"Error tracking upload: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Upload tracking failed'
            })
        }

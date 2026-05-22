import json
import boto3
import os
import urllib.parse
import uuid
from botocore.config import Config

s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))

def lambda_handler(event, context):
    print('API Handler invoked - Raw event:', json.dumps(event))
    
    try:
        # Parse the request
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method') or 'GET'
        body = {}
        
        # Parse body if present
        if 'body' in event and event['body']:
            try:
                body_str = event['body']
                if event.get('isBase64Encoded', False):
                    import base64
                    body_str = base64.b64decode(body_str).decode('utf-8')
                body = json.loads(body_str)
            except:
                body = {}
        
        # Handle different endpoints
        if http_method == 'OPTIONS':
            # CORS preflight response
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': ''
            }
        
        elif http_method == 'POST':
            action = body.get('action', '')
            
            if action == 'test':
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'message': 'API is working!',
                        'timestamp': context.aws_request_id,
                        'endpoint': 'test'
                    })
                }
            
            elif action == 'getPresignedUploadUrl':
                return generate_presigned_url_response(body)
            
            else:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Invalid action',
                        'validActions': ['test', 'getPresignedUploadUrl']
                    })
                }
        
        elif http_method == 'GET':
            # Handle GET request for download URLs
            query_params = event.get('queryStringParameters', {}) or {}
            key = query_params.get('key', '')
            
            if not key:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Key parameter required for downloads',
                        'example': '/upload?key=processed/job_id/1080p/image.jpg'
                    })
                }
            
            # Generate download URL
            output_bucket = os.environ.get('OUTPUT_BUCKET', 'output-bucket-image-compressor')
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': output_bucket, 'Key': key},
                ExpiresIn=3600
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'url': presigned_url,
                    'key': key,
                    'expiresIn': 3600,
                    'message': 'Download URL generated'
                })
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        print('Error in Lambda handler:', str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e), 'message': 'Internal server error'})
        }

def generate_presigned_url_response(body):
    """Generate presigned URL for S3 upload"""
    try:
        file_name = body.get('fileName', 'upload.jpg')
        file_type = body.get('fileType', 'image/jpeg')
        # Allow client to specify job_id and folder (e.g., '1080p', '720p', 'original')
        client_job_id = body.get('jobId')
        folder = body.get('folder', 'original')
        
        # Generate unique jobId if not provided
        job_id = client_job_id if client_job_id else str(uuid.uuid4())
        
        base_name, ext = os.path.splitext(file_name)
        # Sanitize basename to avoid issues
        import re
        base_name = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)
        safe_file_name = f"{base_name}{ext}"
        
        # Get bucket from environment. 
        # If client is uploading processed images, we can upload directly to OUTPUT_BUCKET,
        # but to keep things simple with existing IAM roles, we'll use the environment variable
        # or fall back to the same bucket.
        upload_bucket = os.environ.get('OUTPUT_BUCKET', os.environ.get('INPUT_BUCKET', 'output-bucket-image-compressor'))
        
        # Construct the key path
        if folder == 'original':
            target_key = f"uploads/{job_id}/{safe_file_name}"
        else:
            target_key = f"processed/{job_id}/{folder}/{safe_file_name}"
            
        print(f'Generating presigned URL for {target_key}')
        
        # Generate presigned POST data
        presigned_post = s3_client.generate_presigned_post(
            Bucket=upload_bucket,
            Key=target_key,
            Fields={"Content-Type": file_type},
            Conditions=[
                ["starts-with", "$Content-Type", "image/"],
                ["content-length-range", 0, 10485760]  # 10MB
            ],
            ExpiresIn=3600
        )
        
        response_data = {
            'uploadUrl': presigned_post['url'],
            'fields': presigned_post['fields'],
            'fileUrl': target_key,
            'fileName': safe_file_name,
            'jobId': job_id,
            'folder': folder,
            'message': 'Presigned URL generated successfully',
            'expiresIn': 3600
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print('Error generating presigned URL:', str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e), 'message': 'Failed to generate upload URL'})
        }

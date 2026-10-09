"""
get-upload-url/handler.py

GET /api/card-upload-url
Returns a presigned S3 PUT URL + the object key.
Frontend uploads the image directly to S3 — never touches Lambda bandwidth.
"""

import json
import os
import uuid
import boto3
from botocore.config import Config

BUCKET = os.environ.get('CARD_SCAN_BUCKET', 'gcoffice-card-scans')
REGION = os.environ.get('AWS_REGION_NAME', 'us-east-1')

s3 = boto3.client('s3', region_name=REGION, config=Config(signature_version='s3v4'))

def handler(event, context):
    try:
        key = f"uploads/{uuid.uuid4().hex}.jpg"
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET, 'Key': key, 'ContentType': 'image/jpeg'},
            ExpiresIn=300,
        )
        return respond(200, {'url': url, 'key': key})
    except Exception as e:
        print(f'Error: {e}')
        return respond(500, {'error': 'Could not generate upload URL'})

def respond(status, body):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(body),
    }

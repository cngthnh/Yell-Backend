import logging
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
import os
from flask import copy_current_request_context
import threading


class S3Handler(object):

    def __init__(self):

        self.id_key = os.environ['AWS_ACCESS_KEY']
        self.secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        self.bucket_name = os.environ['AWS_S3_BUCKET_NAME']

        self.client = boto3.client('s3',
                                    config=Config(signature_version='s3v4'),
                                   endpoint_url=None,
                                   aws_access_key_id=self.id_key,
                                   aws_secret_access_key=self.secret_key,
                                   region_name='us-west-2'
                                   )

    def upload(self, file_name, task_id, object_name):

        try:
            self.client.upload_file(file_name, self.bucket_name, task_id + "/" + object_name, ExtraArgs={'CacheControl': 'no-cache'})
            
        except ClientError as e:
            logging.error(e)
    
    def getLink(self, task_id, object_name, expiration=3600): # 3600 = 1 hour
        try:
            response = self.client.generate_presigned_url('get_object', 
                                                            Params={'Bucket': self.bucket_name,
                                                            'Key': task_id + "/" + object_name},
                                                            ExpiresIn=expiration)
        except ClientError as e:
            logging.error(e)
            return None
        return response

    def uploadAsync(self, task_id, object_name):
        @copy_current_request_context
        def sendMessage(task_id, object_name):
            self.upload(task_id, object_name)

        sender = threading.Thread(name='mail_sender', target=sendMessage, args=(task_id, object_name,))
        sender.start()
"""
MUST READ:
S3 presigned URL didn't work for 'ap-south-1' region while it worked for us-east-1.

Try method in create_presigned_url function as the work around.

More info: https://github.com/boto/boto3/issues/3015

"""

import logging

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from decouple import config
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Class to define the storage location
    """

    location = "media"
    file_overwrite = False


def create_presigned_url(bucket_name, bucket_key, expiration=600):
    """
    Generate a presigned URL for an S3 object.

    Parameters
    ----------
    bucket_name : str
        Name of the S3 bucket.
    bucket_key : str
        Key of the S3 object.
    expiration : int, optional
        Time in seconds for the presigned URL to remain valid, by default 600

    Returns
    -------
    str
        The presigned URL.
    """

    try:
        if bucket_name is None or bucket_key is None:
            logging.error("Bucket Name or Bucket Key is None")
            return None

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=config("AWS_ACCESS_KEY"),
            aws_secret_access_key=config("AWS_SECRET_KEY"),
            region_name=config("AWS_S3_REGION_NAME"),
            config=Config(signature_version="v4"),
        )

        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": bucket_key},
            ExpiresIn=expiration,
            HttpMethod="GET",
        )
    except ClientError as e:
        logging.error(e)
        return None

    return response

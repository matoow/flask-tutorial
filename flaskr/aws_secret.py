# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError
from flaskr import logging
import json


# secret_name         region_name
# dev/flaskr          ap-southeast-2

logger = logging.getLogger(__name__)


def get_secret(secret_name, region_name):

    # secret_name = "dev/flaskr"
    # # region_name = "ap-southeast-2"

    logger.info('retrieving secret %s from region %s', secret_name, region_name)

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.error('error retrieving secret: %s', e)
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']

    logger.info('secret retrieved: %s', secret)

    # Your code goes here.
    return json.loads(secret)

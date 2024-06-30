from django.shortcuts import render


import boto3
import logging


endpoint_url = "s3.ir-thr-at1.arvanstorage.ir"
access_key = "860ab792-ba78-433f-a7d5-831a0da59834"
secret_key = "e152c6b6f0527e23d0abc1f90ea8e61a81d97420b5a812ef621eb2b4bfafb218"


def arvan_authenticator():
    logging.basicConfig(level=logging.INFO)

    try:
        return boto3.resource(
            's3',
            endpoint_url='endpoint_url',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret_key'
        )
    except Exception as exc:
        logging.info(exc)
        return None



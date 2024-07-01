from botocore.exceptions import ClientError
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Object
from users.models import CustomUser

import boto3
import logging
import os

from rest_framework.response import Response

User = get_user_model()

endpoint_url = "https://s3.ir-tbz-sh1.arvanstorage.ir"
access_key = "860ab792-ba78-433f-a7d5-831a0da59834"
secret_key = "e152c6b6f0527e23d0abc1f90ea8e61a81d97420b5a812ef621eb2b4bfafb218"
bucket_name = 'webuifinalprojectbucket'


def arvan_authenticator():
    logging.basicConfig(level=logging.INFO)

    try:
        return boto3.resource(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    except Exception as exc:
        logging.info(exc)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_objects(request):
    user = request.user
    pagination = request.data['pagination']

    objects_owned_or_accessible = Object.objects.filter(Q(owner=user) | Q(users_with_access__in=[user])).distinct()

    serialized_data = [
        {'name': obj.name, 'size': obj.size, 'date': obj.date, 'owner': obj.owner.username, 'extension': obj.extension}
        for obj in objects_owned_or_accessible]

    start_element = 12 * (int(pagination) - 1)
    end_element = 12 * (int(pagination) - 1) + 12

    if end_element > len(serialized_data):
        end_element = len(serialized_data)

    total_objects = len(serialized_data)
    return Response({'serialized_data': serialized_data[start_element:end_element],
                     'total_objects_number': total_objects})


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request):
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['POST'],
                'AllowedOrigins': ['*']
            }]
        }

        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )

        object_name = request.data['object_name']
        response = create_presigned_post(s3_client, bucket_name, object_name)
        if response:
            logging.info(f"response: {response}")
            return Response(response, status=200)
        else:
            raise Exception
    except Exception:
        return Response({'detail': 'Failed to create presigned post to S3.'}, status=500)


def create_presigned_post(s3_client, bucket_name, object_name, fields=None, conditions=None, expiration=3600):
    try:
        return s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration
        )
    except ClientError as e:
        logging.error(e)
        return None


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_upload(request):
    data = request.data
    try:
        file_path = data['file_path']
        object_name = data['object_name']

        if not file_path or not object_name:
            return Response({"error": "file_path and object_name are required."}, status=400)

        extension = os.path.splitext(file_path)[1].lower().strip(".")

        existing_object = Object.objects.filter(name=object_name, owner=request.user).first()
        if existing_object:
            existing_object.delete()

        with open(file_path, "rb") as file:
            owner = request.user
            size = file.tell()
            new_object = Object(
                name=object_name,
                size=size,
                owner=owner,
                extension=extension
            )
            new_object.save()
            new_object.users_with_access.add(owner)
            new_object.save()

            return Response({'detail': 'Changes submitted to database.'}, status=200)

    except Exception as exc:
        logging.error(exc)
        return Response({"error": "Failed to submit required changes to database."}, status=500)


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download(request):
    data = request.data
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        if s3_client is None:
            raise Exception()
    except Exception as exc:
        logging.error(exc)
        return Response({"error": "Authentication to S3 failed."}, status=500)
    else:
        try:
            object_name = data['object_name']

            obj = Object.objects.filter(name=object_name).first()

            if obj is None:
                return Response({"error": "Object not found."}, status=404)

            if request.user != obj.owner and not obj.users_with_access.filter(id=request.user.id).exists():
                return Response({"error": "You do not have permission to access this object."}, status=403)

            response = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': object_name
                },
                ExpiresIn=3600
            )

            return Response({'download_link': response}, status=200)

        except Exception as exc:
            logging.error(exc)
            return Response({"error": "Failed to download object from S3."}, status=500)


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete(request):
    data = request.data
    try:
        s3_resource = arvan_authenticator()
        if s3_resource is None:
            raise Exception()
    except Exception as exc:
        logging.error(exc)
        return Response({"error": "Authentication to S3 failed."}, status=500)
    else:
        try:
            bucket = s3_resource.Bucket(bucket_name)
            object_name = data['object_name']

            db_obj = Object.objects.filter(name=object_name).first()

            if db_obj is None:
                return Response({"error": "Object not found."}, status=404)

            if request.user != db_obj.owner and not db_obj.users_with_access.filter(id=request.user.id).exists():
                return Response({"error": "You do not have permission to access this object."}, status=403)

            bucket_object = bucket.Object(object_name)

            response = bucket_object.delete(
                VersionId='string',
            )

            db_obj.delete()

            return Response({'detail': 'Object deleted successfully'}, status=200)

        except Exception as exc:
            logging.error(exc)
            return Response({"error": "Failed to delete object from Storage."}, status=500)


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_users_access(request):
    data = request.data
    object_name = data.get('object_name')

    if not object_name:
        return Response({'error': 'Object name is required'}, status=400)

    db_obj = Object.objects.filter(name=object_name).first()

    if not db_obj:
        return Response({'error': 'Object not found'}, status=404)

    users = CustomUser.objects.all()
    users_with_access = db_obj.users_with_access.all()

    response = []

    for user in users:
        if user.username != request.user.username:
            response.append({
                'user': user.username,
                'email': user.email,
                'avatar': 'https://saatsheni.com/storage/4a4da2041c057327aa7287ae5e78c2b6/Card-thumbanil-copy.webp',
                'has_access': 'true' if user in users_with_access else 'false'
            })

    return Response(response, status=200)


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_users_access(request):
    data = request.data
    new_permissions = data.get('permissions', [])
    object_name = data.get('object_name')

    if not object_name:
        return Response({'error': 'Object name is required'}, status=400)

    db_obj = Object.objects.filter(name=object_name).first()

    if not db_obj:
        return Response({'error': 'Object not found'}, status=404)

    for permission in new_permissions:
        user = CustomUser.objects.filter(username=permission['user']).first()
        if not user:
            continue

        if permission['allowed'] == 'true':
            db_obj.users_with_access.add(user)
        else:
            db_obj.users_with_access.remove(user)

    return Response({'detail': 'Permissions changed successfully.'}, status=200)

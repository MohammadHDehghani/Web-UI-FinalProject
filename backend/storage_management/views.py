from django.contrib.auth import get_user_model
from django.db.models import Q
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


from .models import Object


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
            endpoint_url= endpoint_url,
            aws_access_key_id= access_key,
            aws_secret_access_key= secret_key
        )
    except Exception as exc:
        logging.info(exc)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_objects(request):
    user = request.user
    pagination = request.data['pagination']

    objects_owned_or_accessible = Object.objects.filter(Q(owner=user) | Q(users_with_access__in=[user])).distinct()

    serialized_data = [{'name': obj.name, 'size': obj.size, 'date': obj.date, 'owner': obj.owner.username, 'extension': obj.extension} for obj in objects_owned_or_accessible]

    start_element = 12*(int(pagination)-1)
    end_element = 12*(int(pagination)-1) + 12

    if end_element > len(serialized_data):
        end_element = len(serialized_data) - 1

    total_objects = len(serialized_data)
    return Response({'serialized_data': serialized_data[start_element:end_element],
                     'total_objects_number': total_objects})


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request):
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
            file_path = data['file_path']
            object_name = data['object_name']

            if not file_path or not object_name:
                return Response({"error": "file_path and object_name are required."})

            extension = os.path.splitext(file_path)[1].lower().strip(".")

            existing_object = Object.objects.filter(name=object_name, owner=request.user).first()
            if existing_object:
                existing_object.delete()

            with open(file_path, "rb") as file:
                bucket.put_object(
                    ACL='private',
                    Body=file,
                    Key=object_name,
                )
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

                return Response({'detail': 'File uploaded successfully.'}, status=200)

        except Exception as exc:
            logging.error(exc)
            return Response({"error": "Failed to upload object to S3."}, status=500)


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download(request):
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
            download_path = data['download_path']
            object_name = data['object_name']

            obj = Object.objects.filter(name=object_name).first()

            if obj is None:
                return Response({"error": "Object not found."}, status=404)

            if request.user != obj.owner and not obj.users_with_access.filter(id=request.user.id).exists():
                return Response({"error": "You do not have permission to access this object."}, status=403)

            bucket.download_file(object_name, download_path)
            return Response({'detail': 'File downloaded successfully.'}, status=200)

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


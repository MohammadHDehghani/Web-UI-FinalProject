import unittest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class MockS3Client:
    def __init__(self):
        self.buckets = {'webuifinalprojectbucket': MagicMock()}

    def generate_presigned_post(self, Bucket, Key, Fields=None, Conditions=None, ExpiresIn=3600):
        return {
            'url': 'https://mock-presigned-url.com',
            'fields': {'key': 'value'}
        }

    def generate_presigned_url(self, method, Params, ExpiresIn):
        return 'https://mock-download-url.com'


class UserObjectsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='StrongPass123!')
        self.client.force_authenticate(user=self.user)

    def test_user_objects(self):
        url = reverse('get_user_objects')
        data = {'pagination': 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('serialized_data', response.data)
        self.assertIn('total_objects_number', response.data)


class UploadTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='StrongPass123!')
        self.client.force_authenticate(user=self.user)

    @patch('boto3.client', MockS3Client)
    def test_upload_null_object_name(self):
        url = reverse('upload')
        data = {'object_name': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('detail', response.data)


if __name__ == '__main__':
    unittest.main()

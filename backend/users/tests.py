from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .tokens import account_activation_token
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


class SignUpTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_signup_invalid_username(self):
        url = reverse('signup')
        data = {
            'username': '',
            'email': 'validemail@example.com',
            'password': '!Qa2cderF'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_invalid_email(self):
        url = reverse('signup')
        data = {
            'username': 'validusername',
            'email': 'invalid_email',
            'password': '!Qa2cderF'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_invalid_password(self):
        url = reverse('signup')
        data = {
            'username': 'validusername',
            'email': 'validemail@example.com',
            'password': 'weakpass'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ActivateTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username='testuser', email='test@example.com')
        self.token = account_activation_token.make_token(self.user)
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_activate_valid_token(self):
        url = reverse('activate', kwargs={'uidb64': self.uidb64, 'token': self.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_activate_invalid_token(self):
        url = reverse('activate', kwargs={'uidb64': self.uidb64, 'token': 'invalid_token'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='StrongPass123!')

    def test_login_invalid_credentials(self):
        url = reverse('login')
        data = {
            'username_email': 'testuser',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

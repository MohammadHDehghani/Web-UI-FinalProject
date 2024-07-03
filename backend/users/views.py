from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.contrib.auth import get_user_model, authenticate
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from django.urls import reverse

from .forms import LoginForm
from .models import CustomUser
from storage_management.models import Object
from .serializers import SignUpSerializer
from .tokens import account_activation_token

import re
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    try:
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_verification_email(request, user)
            return Response({'detail': 'Verification email sent.'}, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Signup validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Signup failed with an exception.")
        return Response({'detail': 'An error occurred during signup.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_verification_email(request, user):
    try:
        current_site = get_current_site(request)
        mail_subject = 'Activate your account.'
        message = render_to_string('acc_active_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        to_email = user.email
        send_mail(mail_subject, message, 'your_email@example.com', [to_email])
    except Exception as e:
        logger.exception("Failed to send verification email.")
        raise e


@csrf_protect
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('http://127.0.0.1:4200/login/')
    else:
        return Response({'detail': 'Activation link is invalid!'}, status=status.HTTP_400_BAD_REQUEST)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    form = LoginForm(request.data)
    if form.is_valid():
        username_or_email = form.cleaned_data['username_email']
        password = form.cleaned_data['password']

        if is_valid_email(username_or_email):
            user = authenticate(request, email=username_or_email, password=password)
        else:
            user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'username': user.username,
                'avatar': 'https://saatsheni.com/storage/4a4da2041c057327aa7287ae5e78c2b6/Card-thumbanil-copy.webp',
                'total_volume': calculate_total_volume(user.username),
            })
        else:
            return Response({'detail': 'Invalid username or password.Or user\' email is not activated.'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


def calculate_total_volume(username):
    objects = Object.objects.all()
    total_volume = 0

    for object in objects:
        if object.owner.username == username:
            total_volume = total_volume + int(object.size)

    return total_volume


def is_valid_email(email):
    pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@csrf_protect
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)

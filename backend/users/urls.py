from django.urls import path
from . import views
from .views import signup, activate

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', signup, name='signup'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
]

from django.urls import path
from .views import user_objects, upload, download, delete, get_users_access, change_users_access


urlpatterns = [
    path('objects/', user_objects, name="get_user_objects"),
    path('upload/', upload, name="upload"),
    path('download/', download, name="download"),
    path('delete/', delete, name="delete"),
    path('users/', get_users_access, name="get_users_access"),
    path('permissions/', change_users_access, name="change_users_access")
]

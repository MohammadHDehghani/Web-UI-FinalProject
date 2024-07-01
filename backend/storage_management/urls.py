from django.urls import path
from .views import user_objects, upload, post_upload, download, delete, get_users_access, change_users_access


urlpatterns = [
    path('objects/', user_objects, name="get_user_objects"),
    path('upload/', upload, name="upload"),
    path('post-upload/', post_upload, name="post_upload"),
    path('download/', download, name="download"),
    path('delete/', delete, name="delete"),
    path('users/', get_users_access, name="get_users_access"),
    path('permissions/', change_users_access, name="change_users_access")
]

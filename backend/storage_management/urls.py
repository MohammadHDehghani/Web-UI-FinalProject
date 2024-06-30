from django.urls import path
from .views import user_objects, upload, download, delete


urlpatterns = [
    path('objects/', user_objects, name="get_user_objects"),
    path('upload/', upload, name="upload"),
    path('download/', download, name="download"),
    path('delete/', delete, name="delete"),
]

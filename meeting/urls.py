from django.urls import path
from .views import index, create_zoom_meeting

app_name = 'meeting'

urlpatterns = [
    path('', index, name='index'),
    path('create-meeting/', create_zoom_meeting, name='create-meeting'),
]

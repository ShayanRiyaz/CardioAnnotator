# annotation/urls.py
from django.urls import path
from .views import annotation

app_name = "annotation"

urlpatterns = [
    path('', annotation, name='annotate'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('predictions/', views.predict_view, name='predictions'),
    path('applications/', views.applications_view, name='applications'),
]
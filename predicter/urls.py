from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_view, name='predict'),
    path('application/', views.applications_view, name='application'),
]
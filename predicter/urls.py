from django.urls import path
from . import views

urlpatterns = [
    path('predictions/', views.predict_view, name='predictions'),
    path('applications/', views.applications_view, name='applications'),
    path('applications/new/', views.create_application, name='create-application'),
    path('applications/<int:id>/', views.application_detail, name='application-detail'),
]
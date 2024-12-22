from django.urls import path
from . import views

urlpatterns = [
    path('predictions/', views.predict_view, name='predictions'),
    path('applications/', views.applications_view, name='applications'),
    path('applications/new/', views.create_application, name='create-application'),
    path('applications/<int:id>/', views.application_detail, name='application-detail'),
    path(
        'applications/<int:application_id>/update-status',
        views.update_application_status,
        name='update-application-status'
    ),
    path(
        'applications/<int:application_id>/change-key',
        views.change_key,
        name='change-key'
    ),
    path('applications/predict/', views.predict_service, name='predict'),
]
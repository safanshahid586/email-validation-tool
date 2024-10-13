from django.urls import path
from . import views

urlpatterns = [
    path('validate/', views.validate_email_view, name='validate_email'),
    path('bulk-validate/', views.validate_emails_in_bulk_view, name='bulk_validate_email'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    path('jobseeker/', views.jobseeker_dashboard, name='jobseeker_dashboard'),
    path('employer/', views.employer_dashboard, name='employer_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]

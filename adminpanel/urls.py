from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.admin_users_view, name='admin_users'),
    path('users/<int:user_id>/<str:action>/', views.admin_user_action_view, name='admin_user_action'),
    path('companies/', views.admin_companies_view, name='admin_companies'),
    path('companies/<int:company_id>/<str:action>/', views.admin_company_action_view, name='admin_company_action'),
    path('jobs/', views.admin_jobs_view, name='admin_jobs'),
    path('jobs/<int:job_id>/<str:action>/', views.admin_job_action_view, name='admin_job_action'),
    path('announcements/', views.admin_announcements_view, name='admin_announcements'),
    path('reports/', views.admin_reports_view, name='admin_reports'),
    path('ai-hub/', views.admin_ai_hub_view, name='admin_ai_hub'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ai_dashboard_view, name='ai_dashboard'),
    path('resume-analyzer/', views.ai_resume_analyzer_view, name='ai_resume_analyzer'),
    path('ats-score/', views.ai_ats_score_view, name='ai_ats_score'),
    path('resume-builder/', views.ai_resume_builder_view, name='ai_resume_builder'),
    path('job-recommendation/', views.ai_job_recommendation_view, name='ai_job_recommendation'),
    path('skill-gap/', views.ai_skill_gap_view, name='ai_skill_gap'),
    path('interview-generator/', views.ai_interview_generator_view, name='ai_interview_generator'),
    path('career-chatbot/', views.ai_career_chatbot_view, name='ai_career_chatbot'),
    path('smart-matching/', views.ai_smart_matching_view, name='ai_smart_matching'),
    path('employer-hub/', views.employer_ai_hub_view, name='employer_ai_hub'),
    path('seeker-hub/', views.seeker_ai_hub_view, name='seeker_ai_hub'),
]

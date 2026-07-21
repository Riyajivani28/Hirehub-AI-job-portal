from django.urls import path
from . import views

urlpatterns = [
    path('apply/<int:job_id>/', views.apply_job_view, name='apply_job'),
    path('my-applications/', views.my_applications_view, name='my_applications'),
    path('candidates/', views.employer_applications_view, name='employer_applications'),
    path('<int:app_id>/status/<str:status>/', views.update_application_status, name='update_application_status'),
    path('<int:app_id>/schedule-interview/', views.schedule_interview_view, name='schedule_interview'),
    path('<int:app_id>/offer-letter/', views.generate_offer_letter_view, name='generate_offer_letter'),
]

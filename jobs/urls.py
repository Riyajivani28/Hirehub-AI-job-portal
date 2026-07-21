from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list_view, name='job_list'),
    path('<int:job_id>/', views.job_detail_view, name='job_detail'),
    path('<int:job_id>/toggle-save/', views.toggle_save_job, name='toggle_save_job'),
    path('post/', views.post_job_view, name='post_job'),
    path('<int:job_id>/edit/', views.edit_job_view, name='edit_job'),
    path('<int:job_id>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),
    path('<int:job_id>/delete/', views.delete_job_view, name='delete_job'),
]

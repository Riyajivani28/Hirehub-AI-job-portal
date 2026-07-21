from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.profile_view, name='profile_user'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/add-education/', views.add_education_view, name='add_education'),
    path('profile/delete-education/<int:edu_id>/', views.delete_education_view, name='delete_education'),
    path('profile/add-experience/', views.add_experience_view, name='add_experience'),
    path('profile/delete-experience/<int:exp_id>/', views.delete_experience_view, name='delete_experience'),
    path('profile/add-skill/', views.add_skill_view, name='add_skill'),
    path('profile/delete-skill/<int:skill_id>/', views.delete_skill_view, name='delete_skill'),
]

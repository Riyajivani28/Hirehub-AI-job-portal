from django.urls import path
from . import views

urlpatterns = [
    path('', views.company_list_view, name='company_list'),
    path('<int:company_id>/', views.company_detail_view, name='company_detail'),
    path('edit/', views.company_edit_view, name='company_edit'),
]

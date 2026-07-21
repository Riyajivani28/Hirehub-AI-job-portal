from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('<int:notif_id>/read/', views.mark_as_read_view, name='mark_notification_read'),
]

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from jobs.views import home_view
from feedback.views import feedback_view, contact_view
from reports import views as report_views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', home_view, name='home'),
    
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('companies/', include('companies.urls')),
    path('applications/', include('applications.urls')),
    path('notifications/', include('notifications.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('ai/', include('ai_features.urls')),
    path('admin-panel/', include('adminpanel.urls')),
    
    path('contact/', contact_view, name='contact'),
    path('feedback/', feedback_view, name='feedback'),
    path('why-choose-us/', report_views.static_why_choose, name='why_choose'),
    path('how-it-works/', report_views.static_how_it_works, name='how_it_works'),
    path('testimonials/', report_views.static_testimonials, name='testimonials'),
    path('career-tips/', report_views.static_career_tips, name='career_tips'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

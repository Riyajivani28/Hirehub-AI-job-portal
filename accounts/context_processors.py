from notifications.models import Notification
from jobs.models import Category
from companies.models import Company

def global_context(request):
    context = {
        'all_categories': Category.objects.all()[:8] if Category.objects.exists() else [],
        'unread_notifications_count': 0,
        'user_company': None
    }
    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(user=request.user, is_read=False).count()
        if request.user.is_employer:
            context['user_company'] = Company.objects.filter(employer=request.user).first()
    return context

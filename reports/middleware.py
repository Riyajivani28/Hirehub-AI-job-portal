from .models import SiteVisitorLog

class TrafficAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip static assets, media files, and favicon to keep logs clean
        path = request.path
        if any(path.startswith(prefix) for prefix in ['/static/', '/media/', '/favicon.ico']):
            return response

        # Categorize action_type automatically based on request URL pattern & method
        action_type = 'Page Visit'
        if '/accounts/login' in path:
            action_type = 'Login'
        elif '/accounts/register' in path:
            action_type = 'Registration'
        elif '/dashboard' in path:
            action_type = 'Dashboard Access'
        elif '/applications' in path or '/apply' in path or 'apply' in request.resolver_match.url_name if request.resolver_match else False:
            action_type = 'Job Application'
        elif '/ai/' in path or '/ai-features/' in path:
            action_type = 'AI Suite Module'

        # Extract client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')

        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown Browser')
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Ensure session key exists if available
        session_key = None
        if hasattr(request, 'session') and request.session.session_key:
            session_key = request.session.session_key

        try:
            SiteVisitorLog.objects.create(
                user=user,
                page_visited=path,
                ip_address=ip_address,
                user_agent=user_agent,
                action_type=action_type,
                session_key=session_key
            )
        except Exception:
            pass

        return response

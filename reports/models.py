from django.db import models

class SystemAnnouncement(models.Model):
    TARGET_CHOICES = (
        ('all', 'All Users'),
        ('jobseeker', 'Job Seekers Only'),
        ('employer', 'Employers Only'),
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    target_role = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

from django.conf import settings

class SiteVisitorLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='traffic_logs')
    page_visited = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    action_type = models.CharField(max_length=50, default='Page View')
    session_key = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_info = self.user.username if self.user else (self.ip_address or 'Anonymous')
        return f"[{self.action_type}] {self.page_visited} by {user_info} at {self.timestamp}"

    @property
    def path(self):
        return self.page_visited

    @property
    def visited_at(self):
        return self.timestamp

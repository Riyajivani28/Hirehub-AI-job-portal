from django.db import models
from django.conf import settings
from jobs.models import Job

class ATSAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ats_analyses')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='ats_evaluations')
    score = models.IntegerField(default=0)
    matched_skills = models.TextField(blank=True, help_text="Comma-separated matched skills")
    missing_skills = models.TextField(blank=True, help_text="Comma-separated missing skills")
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.job.title if self.job else 'Custom Job'} ({self.score}%)"

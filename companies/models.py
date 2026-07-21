from django.db import models
from django.conf import settings

class Company(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    hr_contact_name = models.CharField(max_length=100)
    hr_contact_email = models.EmailField()
    hr_contact_phone = models.CharField(max_length=20)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    is_verified_badge = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def active_jobs_count(self):
        return self.jobs.filter(status='active').count()

    def total_jobs_count(self):
        return self.jobs.count()

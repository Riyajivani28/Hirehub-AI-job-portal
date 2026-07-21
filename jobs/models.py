from django.db import models
from django.conf import settings
from django.utils.text import slugify
from companies.models import Company

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='fa-briefcase')
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('internship', 'Internship'),
        ('fresher', 'Fresher'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('pending_approval', 'Pending Approval'),
        ('flagged', 'Flagged as Fake'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='jobs')
    vacancy = models.IntegerField(default=1)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary_negotiable = models.BooleanField(default=False)
    experience_required = models.CharField(max_length=50, help_text="e.g. 2-4 years")
    qualification = models.CharField(max_length=150)
    skills_required = models.TextField(help_text="Comma-separated skills e.g. Python, Django, React")
    description = models.TextField()
    responsibilities = models.TextField()
    benefits = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=150)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def get_skills_list(self):
        if not self.skills_required:
            return []
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

class SavedJob(models.Model):
    seeker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by_users')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('seeker', 'job')

    def __str__(self):
        return f"{self.seeker.username} saved {self.job.title}"

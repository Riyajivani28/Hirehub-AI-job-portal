from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('jobseeker', 'Job Seeker'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='jobseeker')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_jobseeker(self):
        return self.role == 'jobseeker'

    @property
    def is_employer(self):
        return self.role == 'employer'

    @property
    def is_site_admin(self):
        return self.role == 'admin' or self.is_superuser

class JobSeekerProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not', 'Prefer not to say'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seeker_profile')
    headline = models.CharField(max_length=255, blank=True, null=True, help_text="Full Stack Python Developer")
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default='India')
    expected_salary = models.CharField(max_length=100, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    resume_ats_score = models.IntegerField(default=75)
    
    @property
    def resume_views(self):
        return 12 + (self.user.applications.count() * 3 if hasattr(self.user, 'applications') else 0)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"

    def calculate_completion(self):
        fields = [self.headline, self.dob, self.gender, self.address, self.city, self.resume, self.linkedin_url]
        filled = sum(1 for f in fields if f)
        base = int((filled / len(fields)) * 60)
        has_edu = self.education_set.exists()
        has_exp = self.experience_set.exists()
        has_skills = self.skills.exists()
        total = base + (15 if has_edu else 0) + (15 if has_exp else 0) + (10 if has_skills else 0)
        return min(100, total)

class Education(models.Model):
    seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='education_set')
    degree = models.CharField(max_length=150)
    institution = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=150, blank=True, null=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField(blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.degree} at {self.institution}"

class Experience(models.Model):
    seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='experience_set')
    title = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150)
    location = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, default='Technical')

    def __str__(self):
        return self.name

class JobSeekerSkill(models.Model):
    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    )
    seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='intermediate')

    class Meta:
        unique_together = ('seeker', 'skill')

    def __str__(self):
        return f"{self.seeker.user.username} - {self.skill.name}"

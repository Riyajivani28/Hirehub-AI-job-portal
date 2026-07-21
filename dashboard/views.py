from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import User, JobSeekerProfile
from jobs.models import Job, SavedJob, Category
from companies.models import Company
from applications.models import Application, Interview
from notifications.models import Notification
from reports.models import SystemAnnouncement, SiteVisitorLog
from feedback.models import Feedback, ContactMessage
from django.db.models import Count, Q, Sum

@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_site_admin:
        return redirect('admin_dashboard')
    elif user.is_employer:
        return redirect('employer_dashboard')
    else:
        return redirect('jobseeker_dashboard')

@login_required
def jobseeker_dashboard(request):
    if not request.user.is_jobseeker:
        return redirect('dashboard_redirect')

    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
    completion_pct = profile.calculate_completion()

    applied_apps = Application.objects.filter(applicant=request.user).select_related('job', 'job__company')[:5]
    saved_jobs = SavedJob.objects.filter(seeker=request.user).select_related('job', 'job__company')[:5]
    interviews = Interview.objects.filter(application__applicant=request.user, status='scheduled')

    # AI Recommendation simulation based on skills
    seeker_skill_names = set(profile.skills.values_list('skill__name', flat=True))
    all_jobs = Job.objects.filter(status='active').select_related('company', 'category')
    recommended_jobs = []
    for j in all_jobs:
        job_skills = set([s.strip().lower() for s in j.skills_required.split(',') if s.strip()])
        if any(s.lower() in job_skills for s in seeker_skill_names) or not seeker_skill_names:
            recommended_jobs.append(j)

    stats = {
        'applied_count': Application.objects.filter(applicant=request.user).count(),
        'saved_count': SavedJob.objects.filter(seeker=request.user).count(),
        'recommended_count': len(recommended_jobs),
        'resume_views': profile.resume_views,
        'interview_calls': interviews.count(),
        'notifications_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        'completion_pct': completion_pct
    }

    announcements = SystemAnnouncement.objects.filter(is_active=True, target_role__in=['all', 'jobseeker'])[:3]

    return render(request, 'dashboard/jobseeker_dashboard.html', {
        'stats': stats,
        'profile': profile,
        'applied_apps': applied_apps,
        'saved_jobs': saved_jobs,
        'recommended_jobs': recommended_jobs[:4],
        'interviews': interviews,
        'announcements': announcements
    })

@login_required
def employer_dashboard(request):
    if not request.user.is_employer:
        return redirect('dashboard_redirect')

    company = Company.objects.filter(employer=request.user).first()
    jobs = Job.objects.filter(posted_by=request.user).select_related('category')
    applications = Application.objects.filter(job__posted_by=request.user)

    stats = {
        'total_jobs': jobs.count(),
        'active_jobs': jobs.filter(status='active').count(),
        'total_applications': applications.count(),
        'interviews_scheduled': Interview.objects.filter(application__job__posted_by=request.user, status='scheduled').count(),
        'selected_candidates': applications.filter(status='selected').count(),
    }

    recent_applications = applications.select_related('job', 'applicant', 'applicant__seeker_profile').order_by('-applied_at')[:6]
    announcements = SystemAnnouncement.objects.filter(is_active=True, target_role__in=['all', 'employer'])[:3]

    return render(request, 'dashboard/employer_dashboard.html', {
        'company': company,
        'jobs': jobs,
        'stats': stats,
        'recent_applications': recent_applications,
        'announcements': announcements
    })

@login_required
def admin_dashboard(request):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    stats = {
        'total_users': User.objects.count(),
        'total_companies': Company.objects.count(),
        'verified_companies': Company.objects.filter(verification_status='approved').count(),
        'active_jobs': Job.objects.filter(status='active').count(),
        'total_applications': Application.objects.count(),
        'pending_company_verifications': Company.objects.filter(verification_status='pending').count(),
        'reported_jobs': Job.objects.filter(status='flagged').count(),
        'daily_visitors': SiteVisitorLog.objects.count(),
    }

    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_companies = Company.objects.order_by('-created_at')[:5]
    recent_jobs = Job.objects.select_related('company', 'posted_by').order_by('-created_at')[:8]
    pending_companies = Company.objects.filter(verification_status='pending').order_by('-created_at')[:5]
    pending_feedbacks = Feedback.objects.order_by('-created_at')[:5]

    return render(request, 'dashboard/admin_dashboard.html', {
        'stats': stats,
        'recent_users': recent_users,
        'recent_companies': recent_companies,
        'recent_jobs': recent_jobs,
        'pending_companies': pending_companies,
        'pending_feedbacks': pending_feedbacks
    })

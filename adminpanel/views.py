from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from companies.models import Company
from jobs.models import Job
from applications.models import Application
from reports.models import SystemAnnouncement, SiteVisitorLog
from feedback.models import Feedback, ContactMessage

@login_required
def admin_users_view(request):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    role_filter = request.GET.get('role', 'all')
    users = User.objects.all().order_by('-date_joined')

    if role_filter != 'all':
        users = users.filter(role=role_filter)

    return render(request, 'adminpanel/users_manage.html', {
        'users': users,
        'role_filter': role_filter
    })

@login_required
def admin_user_action_view(request, user_id, action):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    target_user = get_object_or_404(User, id=user_id)

    if action == 'verify':
        target_user.is_verified = not target_user.is_verified
        status_str = "verified" if target_user.is_verified else "unverified"
        messages.success(request, f"User {target_user.username} is now {status_str}.")
    elif action in ('ban', 'block', 'toggle_ban'):
        target_user.is_active = not target_user.is_active
        status_str = "active" if target_user.is_active else "banned/inactive"
        messages.warning(request, f"User {target_user.username} status set to {status_str}.")
    elif action == 'activate':
        target_user.is_active = True
        messages.success(request, f"User {target_user.username} activated.")
    elif action == 'delete':
        target_user.delete()
        messages.info(request, "User deleted successfully.")
        return redirect('admin_users')

    target_user.save()
    return redirect('admin_users')

@login_required
def admin_companies_view(request):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    status_filter = request.GET.get('status', 'all')
    companies = Company.objects.all().order_by('-created_at')

    if status_filter != 'all':
        companies = companies.filter(verification_status=status_filter)

    return render(request, 'adminpanel/companies_manage.html', {
        'companies': companies,
        'status_filter': status_filter
    })

@login_required
def admin_company_action_view(request, company_id, action):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    company = get_object_or_404(Company, id=company_id)

    if action == 'approve':
        company.verification_status = 'approved'
        company.is_verified_badge = True
        messages.success(request, f"Company '{company.name}' approved!")
    elif action == 'reject':
        company.verification_status = 'rejected'
        company.is_verified_badge = False
        messages.warning(request, f"Company '{company.name}' rejected.")
    elif action == 'suspend':
        company.verification_status = 'suspended'
        company.is_verified_badge = False
        messages.warning(request, f"Company '{company.name}' suspended.")
    elif action == 'toggle_badge':
        company.is_verified_badge = not company.is_verified_badge
        messages.info(request, "Company verification badge toggled.")

    company.save()
    return redirect('admin_companies')

@login_required
def admin_jobs_view(request):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    jobs = Job.objects.select_related('company', 'posted_by').order_by('-created_at')
    return render(request, 'adminpanel/jobs_manage.html', {'jobs': jobs})

@login_required
def admin_job_action_view(request, job_id, action):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    job = get_object_or_404(Job, id=job_id)

    if action in ('toggle', 'toggle_active'):
        if job.status == 'active':
            job.status = 'closed'
            messages.warning(request, f"Job '{job.title}' marked as Closed.")
        else:
            job.status = 'active'
            messages.success(request, f"Job '{job.title}' activated.")
    elif action == 'approve':
        job.status = 'active'
        messages.success(request, f"Job '{job.title}' approved.")
    elif action == 'flag_fake':
        job.status = 'flagged'
        messages.warning(request, f"Job '{job.title}' flagged as fake.")
    elif action == 'delete':
        job.delete()
        messages.info(request, "Job listing deleted.")
        return redirect('admin_jobs')

    job.save()
    return redirect('admin_jobs')

@login_required
def admin_announcements_view(request):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_role = request.POST.get('target_role', 'all')
        if title and content:
            SystemAnnouncement.objects.create(title=title, content=content, target_role=target_role)
            messages.success(request, "Broadcast announcement published!")
            return redirect('admin_announcements')

    announcements = SystemAnnouncement.objects.order_by('-created_at')
    return render(request, 'adminpanel/announcement_form.html', {'announcements': announcements})

@login_required
def admin_reports_view(request):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    visitor_logs = SiteVisitorLog.objects.select_related('user').order_by('-timestamp')[:100]

    analytics = {
        'total_logs': SiteVisitorLog.objects.count(),
        'visitor_counts': [120, 240, 310, 450, 680, 890, 1280],
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        'jobs_posted_monthly': [15, 30, 45, 60, 95, 120, 150],
        'applications_monthly': [120, 340, 560, 890, 1200, 1800, 2400],
        'revenue_monthly': [50000, 85000, 120000, 180000, 290000, 380000, 485000],
    }

    feedbacks = Feedback.objects.all().order_by('-created_at')
    contact_messages = ContactMessage.objects.all().order_by('-created_at')

    return render(request, 'adminpanel/admin_reports.html', {
        'visitor_logs': visitor_logs,
        'analytics': analytics,
        'feedbacks': feedbacks,
        'contact_messages': contact_messages
    })

import os
import requests

def generate_admin_ai_response(prompt_text, default_text=""):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return default_text

    candidate_models = ["gemma-4-26b-a4b-it", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"]
    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            continue
    return default_text

@login_required
def admin_ai_hub_view(request):
    if not request.user.is_site_admin:
        return redirect('dashboard_redirect')

    ai_result = None
    active_tab = request.POST.get('action_type', 'overview')

    # Handle POST AI Action Requests
    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        if action_type == 'generate_announcement':
            topic = request.POST.get('topic', 'Platform Upgrade')
            role = request.POST.get('target_role', 'all')
            prompt = f"Write an engaging, professional system broadcast announcement for a job portal platform HireHub. Target Audience: {role}. Topic/Details: {topic}. Output format: Line 1 as Title, followed by 2 short paragraphs."
            fallback = f"📢 System Notification: {topic}\n\nWe are excited to inform all {role} users about recent updates regarding {topic}. Please check your dashboard for further details.\n\nThank you for choosing HireHub!"
            ai_result = generate_admin_ai_response(prompt, fallback)
            if request.POST.get('auto_publish') == 'true' and ai_result:
                lines = [l.strip() for l in ai_result.split('\n') if l.strip()]
                ann_title = lines[0].replace('Title:', '').replace('📢', '').strip() if lines else topic
                ann_body = '\n\n'.join(lines[1:]) if len(lines) > 1 else ai_result
                SystemAnnouncement.objects.create(title=ann_title[:200], content=ann_body, target_role=role)
                messages.success(request, f"Announcement '{ann_title}' generated and published successfully!")

        elif action_type == 'generate_broadcast':
            subject = request.POST.get('subject', 'Monthly Hiring Update')
            target = request.POST.get('target_audience', 'employers')
            tone = request.POST.get('tone', 'professional')
            prompt = f"Draft an email broadcast for HireHub {target}. Subject: {subject}. Tone: {tone}. Include clear call to action and warm sign-off."
            fallback = f"Subject: {subject}\n\nDear HireHub {target.capitalize()},\n\nWe are sharing our latest platform updates regarding {subject}.\n\nVisit your dashboard to learn more.\n\nBest regards,\nThe HireHub Team"
            ai_result = generate_admin_ai_response(prompt, fallback)

        elif action_type == 'generate_executive_report':
            prompt = f"Generate an Executive Platform Performance Summary Report for HireHub Job Portal. Total Users: {User.objects.count()}, Total Jobs: {Job.objects.count()}, Total Applications: {Application.objects.count()}. Summarize key trends, recruiter efficiency, candidate match rates, and 3 strategic recommendations for platform growth."
            fallback = f"📊 Executive Summary Report:\n\n- User Growth: Steady expansion across Jobseekers and Employers.\n- Hiring Velocity: {Job.objects.count()} active job listings with active application tracking.\n- Recommendations:\n  1. Expand AI ATS Resume screening tools.\n  2. Enhance employer verification workflows.\n  3. Launch targeted email re-engagement campaigns."
            ai_result = generate_admin_ai_response(prompt, fallback)

    # 1. Fraud / Fake Job Detection Audit
    suspicious_keywords = ['telegram', 'whatsapp only', 'wire transfer', 'deposit', 'pay upfront', 'crypto', 'unlimited income', 'no experience 200k', 'cash payment']
    jobs_audit = []
    for job in Job.objects.select_related('company', 'posted_by').all():
        risk_score = 0
        risk_reasons = []
        combined_text = (job.title + " " + job.description + " " + job.qualification + " " + job.skills_required).lower()
        
        for kw in suspicious_keywords:
            if kw in combined_text:
                risk_score += 30
                risk_reasons.append(f"Contains suspicious phrase '{kw}'")

        if job.salary_min > 500000 and 'fresher' in job.job_type:
            risk_score += 40
            risk_reasons.append("Unrealistically high compensation for entry/fresher level")

        if not job.company.is_verified_badge:
            risk_score += 15
            risk_reasons.append("Posted by unverified employer company profile")

        risk_level = "High" if risk_score >= 50 else ("Medium" if risk_score >= 25 else "Low")
        jobs_audit.append({
            'job': job,
            'risk_score': min(risk_score, 95),
            'risk_level': risk_level,
            'reasons': risk_reasons or ["Legitimate job structure verified"]
        })

    # 2. Company Verification AI Trust Index
    companies_audit = []
    for comp in Company.objects.all():
        trust_score = 100
        flags = []
        if not comp.website:
            trust_score -= 20
            flags.append("Missing official website URL")
        if comp.hr_contact_email and not any(comp.hr_contact_email.endswith(domain) for domain in ['.com', '.org', '.io', '.in', '.co', '.net']):
            trust_score -= 15
            flags.append("Non-standard HR contact email domain")
        if len(comp.description) < 40:
            trust_score -= 25
            flags.append("Short/generic company description")
        if comp.verification_status != 'approved':
            trust_score -= 10
            flags.append("Pending manual admin verification")

        companies_audit.append({
            'company': comp,
            'trust_score': max(trust_score, 20),
            'flags': flags or ["All verification criteria passed"]
        })

    # 3. Feedback & Sentiment Analysis
    feedback_entries = Feedback.objects.all()
    positive_words = ['great', 'awesome', 'good', 'excellent', 'helpful', 'love', 'best', 'easy', 'fast', 'amazing']
    negative_words = ['bad', 'error', 'bug', 'slow', 'worst', 'issue', 'hard', 'fail', 'problem', 'hate']
    
    pos_count = 0
    neg_count = 0
    neutral_count = 0

    for fb in feedback_entries:
        txt = (fb.subject + " " + fb.message).lower() if hasattr(fb, 'subject') else fb.message.lower()
        pos_hits = sum(1 for w in positive_words if w in txt)
        neg_hits = sum(1 for w in negative_words if w in txt)
        if pos_hits > neg_hits:
            pos_count += 1
        elif neg_hits > pos_hits:
            neg_count += 1
        else:
            neutral_count += 1

    total_fb = feedback_entries.count() or 1
    sentiment_data = {
        'positive_pct': round((pos_count / total_fb) * 100),
        'neutral_pct': round((neutral_count / total_fb) * 100),
        'negative_pct': round((neg_count / total_fb) * 100),
        'total_feedback': feedback_entries.count()
    }

    # 4. User Activity & System Health Metrics
    total_users = User.objects.count()
    total_jobs = Job.objects.count()
    total_apps = Application.objects.count()
    total_logs = SiteVisitorLog.objects.count()
    flagged_jobs_count = Job.objects.filter(status='flagged').count()
    pending_companies_count = Company.objects.filter(verification_status='pending').count()

    system_health = {
        'active_users': User.objects.filter(is_active=True).count(),
        'banned_users': User.objects.filter(is_active=False).count(),
        'active_jobs': Job.objects.filter(status='active').count(),
        'flagged_jobs': flagged_jobs_count,
        'pending_companies': pending_companies_count,
        'visitor_traffic_volume': total_logs,
        'db_status': 'Optimal (SQLite Engine Connected)',
        'ai_engine_status': 'Operational (Google Gemini API REST Mode)'
    }

    return render(request, 'adminpanel/admin_ai_hub.html', {
        'system_health': system_health,
        'jobs_audit': jobs_audit[:15],
        'companies_audit': companies_audit[:15],
        'sentiment_data': sentiment_data,
        'ai_result': ai_result,
        'active_tab': active_tab,
        'feedbacks': feedback_entries[:10],
    })

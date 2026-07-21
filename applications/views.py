from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Application, Interview, OfferLetter
from .forms import ApplicationApplyForm, InterviewScheduleForm, OfferLetterForm
from jobs.models import Job
from notifications.models import Notification
from accounts.models import JobSeekerProfile

@login_required
def apply_job_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if not request.user.is_jobseeker:
        messages.error(request, "Only Job Seekers can apply for job vacancies.")
        return redirect('job_detail', job_id=job.id)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already submitted an application for this position.")
        return redirect('job_detail', job_id=job.id)

    profile = getattr(request.user, 'seeker_profile', None)

    if request.method == 'POST':
        form = ApplicationApplyForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.job = job
            app.applicant = request.user
            if not app.resume and profile and profile.resume:
                app.resume = profile.resume
            
            # Simple AI ATS calculation simulation based on skill overlap
            seeker_skills = set(profile.skills.values_list('skill__name', flat=True)) if profile else set()
            job_skills = set([s.strip().lower() for s in job.skills_required.split(',') if s.strip()])
            matches = sum(1 for s in seeker_skills if s.lower() in job_skills)
            score = min(98, max(65, 70 + matches * 8))
            app.ats_match_score = score

            app.save()

            # Notify Employer
            Notification.objects.create(
                user=job.posted_by,
                title=f"New Application for {job.title}",
                message=f"{request.user.get_full_name() or request.user.username} submitted an application with ATS match score {score}%.",
                notification_type='application_status'
            )

            messages.success(request, f"Application for {job.title} successfully sent!")
            return redirect('my_applications')
    else:
        form = ApplicationApplyForm()

    return render(request, 'applications/apply_modal.html', {
        'form': form,
        'job': job,
        'profile': profile
    })

@login_required
def my_applications_view(request):
    if not request.user.is_jobseeker:
        return redirect('dashboard_redirect')

    status_filter = request.GET.get('status', 'all')
    applications = Application.objects.filter(applicant=request.user).select_related('job', 'job__company')

    if status_filter != 'all':
        applications = applications.filter(status=status_filter)

    counts = {
        'all': Application.objects.filter(applicant=request.user).count(),
        'applied': Application.objects.filter(applicant=request.user, status='applied').count(),
        'under_review': Application.objects.filter(applicant=request.user, status='under_review').count(),
        'shortlisted': Application.objects.filter(applicant=request.user, status='shortlisted').count(),
        'interview_scheduled': Application.objects.filter(applicant=request.user, status='interview_scheduled').count(),
        'selected': Application.objects.filter(applicant=request.user, status='selected').count(),
        'rejected': Application.objects.filter(applicant=request.user, status='rejected').count(),
    }

    return render(request, 'applications/my_applications.html', {
        'applications': applications,
        'status_filter': status_filter,
        'counts': counts
    })

@login_required
def employer_applications_view(request):
    if not request.user.is_employer:
        return redirect('dashboard_redirect')

    job_id = request.GET.get('job')
    status_filter = request.GET.get('status', 'all')

    user_jobs = Job.objects.filter(posted_by=request.user)
    applications = Application.objects.filter(job__posted_by=request.user).select_related('job', 'applicant', 'applicant__seeker_profile')

    if job_id:
        applications = applications.filter(job_id=job_id)

    if status_filter != 'all':
        applications = applications.filter(status=status_filter)

    return render(request, 'applications/candidate_applications.html', {
        'applications': applications,
        'user_jobs': user_jobs,
        'selected_job': job_id,
        'status_filter': status_filter
    })

@login_required
def update_application_status(request, app_id, status):
    app = get_object_or_404(Application, id=app_id)
    if not (request.user == app.job.posted_by or request.user.is_site_admin):
        messages.error(request, "Permission denied.")
        return redirect('dashboard_redirect')

    app.status = status
    app.save()

    # Create user notification
    status_display = dict(Application.STATUS_CHOICES).get(status, status)
    Notification.objects.create(
        user=app.applicant,
        title=f"Application Update: {app.job.title}",
        message=f"Your application status for {app.job.title} at {app.job.company.name} was updated to '{status_display}'.",
        notification_type='application_status'
    )

    messages.success(request, f"Updated candidate status to '{status_display}'.")

    if status == 'interview_scheduled':
        return redirect('schedule_interview', app_id=app.id)

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'employer_applications')

@login_required
def schedule_interview_view(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if not (request.user == app.job.posted_by or request.user.is_site_admin):
        messages.error(request, "Permission denied.")
        return redirect('dashboard_redirect')

    interview = getattr(app, 'interview', None)

    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST, instance=interview)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.application = app
            inv.save()

            app.status = 'interview_scheduled'
            app.save()

            Notification.objects.create(
                user=app.applicant,
                title="Interview Invitation Scheduled!",
                message=f"You have been invited for an interview for {app.job.title} at {app.job.company.name} on {inv.scheduled_date.strftime('%B %d, %Y at %H:%M')}.",
                notification_type='interview_scheduled'
            )

            messages.success(request, "Interview successfully scheduled & candidate notified!")
            return redirect('employer_applications')
    else:
        form = InterviewScheduleForm(instance=interview)

    return render(request, 'applications/schedule_interview.html', {
        'form': form,
        'app': app,
        'interview': interview
    })

@login_required
def generate_offer_letter_view(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    offer = getattr(app, 'offer_letter', None)

    if request.user.is_employer or request.user.is_site_admin:
        if request.method == 'POST':
            form = OfferLetterForm(request.POST, instance=offer)
            if form.is_valid():
                off = form.save(commit=False)
                off.application = app
                off.save()

                app.status = 'selected'
                app.save()

                Notification.objects.create(
                    user=app.applicant,
                    title="Congratulations! Offer Letter Received",
                    message=f"You have received an official Job Offer for {app.job.title} at {app.job.company.name}!",
                    notification_type='offer_received'
                )

                messages.success(request, "Offer letter generated and sent to candidate!")
                return redirect('generate_offer_letter', app_id=app.id)
        else:
            default_content = f"Dear {app.applicant.get_full_name() or app.applicant.username},\n\nWe are pleased to offer you the position of {app.job.title} at {app.job.company.name}. We were thoroughly impressed with your skills and background.\n\nBest regards,\n{app.job.company.hr_contact_name}\n{app.job.company.name}"
            form = OfferLetterForm(instance=offer, initial={'content': default_content, 'offered_salary': app.job.salary_max})

        return render(request, 'applications/offer_letter.html', {
            'form': form,
            'app': app,
            'offer': offer,
            'is_employer': True
        })

    elif request.user == app.applicant:
        return render(request, 'applications/offer_letter.html', {
            'app': app,
            'offer': offer,
            'is_employer': False
        })
    else:
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard_redirect')

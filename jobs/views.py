from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Job, Category, SavedJob
from .forms import JobForm
from companies.models import Company
from feedback.models import Feedback
from accounts.models import User

def home_view(request):
    categories = Category.objects.annotate(job_count=Count('jobs')).filter(job_count__gt=0)[:8]
    if not categories.exists():
        categories = Category.objects.all()[:8]

    featured_jobs = Job.objects.filter(status='active').select_related('company', 'category')[:6]
    latest_jobs = Job.objects.filter(status='active').select_related('company', 'category')[:6]
    top_companies = Company.objects.filter(verification_status='approved')[:6]
    testimonials = Feedback.objects.filter(rating__gte=4)[:4]

    stats = {
        'total_jobs': Job.objects.filter(status='active').count(),
        'total_companies': Company.objects.filter(verification_status='approved').count(),
        'total_seekers': User.objects.filter(role='jobseeker').count(),
        'successful_hires': 1420
    }

    return render(request, 'jobs/home.html', {
        'categories': categories,
        'featured_jobs': featured_jobs,
        'latest_jobs': latest_jobs,
        'top_companies': top_companies,
        'testimonials': testimonials,
        'stats': stats
    })

def job_list_view(request):
    jobs = Job.objects.filter(status='active').select_related('company', 'category')

    # Filtering parameters
    keyword = request.GET.get('keyword', '').strip()
    category_id = request.GET.get('category', '')
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '')
    experience = request.GET.get('experience', '')
    min_salary = request.GET.get('min_salary', '')

    if keyword:
        jobs = jobs.filter(
            Q(title__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(skills_required__icontains=keyword) |
            Q(company__name__icontains=keyword)
        )

    if category_id:
        jobs = jobs.filter(category_id=category_id)

    if location:
        jobs = jobs.filter(location__icontains=location)

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    if experience:
        jobs = jobs.filter(experience_required__icontains=experience)

    if min_salary:
        try:
            jobs = jobs.filter(salary_max__gte=float(min_salary))
        except ValueError:
            pass

    # Saved jobs list for authenticated seekers
    saved_job_ids = []
    if request.user.is_authenticated and request.user.is_jobseeker:
        saved_job_ids = list(SavedJob.objects.filter(seeker=request.user).values_list('job_id', flat=True))

    paginator = Paginator(jobs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_categories = Category.objects.all()

    return render(request, 'jobs/job_list.html', {
        'page_obj': page_obj,
        'total_count': jobs.count(),
        'all_categories': all_categories,
        'saved_job_ids': saved_job_ids,
        'keyword': keyword,
        'category_id': category_id,
        'location': location,
        'job_type': job_type,
        'experience': experience,
        'min_salary': min_salary
    })

def job_detail_view(request, job_id):
    job = get_object_or_404(Job.objects.select_related('company', 'category'), id=job_id)
    job.views_count += 1
    job.save(update_fields=['views_count'])

    is_saved = False
    has_applied = False

    if request.user.is_authenticated and request.user.is_jobseeker:
        is_saved = SavedJob.objects.filter(seeker=request.user, job=job).exists()
        has_applied = job.applications.filter(applicant=request.user).exists()

    similar_jobs = Job.objects.filter(category=job.category, status='active').exclude(id=job.id)[:3]

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'is_saved': is_saved,
        'has_applied': has_applied,
        'similar_jobs': similar_jobs
    })

@login_required
def toggle_save_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if not request.user.is_jobseeker:
        messages.warning(request, "Only Job Seekers can bookmark jobs.")
        return redirect('job_detail', job_id=job.id)

    saved_item = SavedJob.objects.filter(seeker=request.user, job=job)
    if saved_item.exists():
        saved_item.delete()
        messages.info(request, f"Removed '{job.title}' from your saved jobs.")
    else:
        SavedJob.objects.create(seeker=request.user, job=job)
        messages.success(request, f"Bookmarked '{job.title}'!")

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'job_list')

@login_required
def post_job_view(request):
    if not request.user.is_employer:
        messages.error(request, "Access restricted. Employer account required to post jobs.")
        return redirect('dashboard_redirect')

    company = Company.objects.filter(employer=request.user).first()
    if not company:
        messages.warning(request, "Please create your Company Profile before posting job vacancies.")
        return redirect('company_edit')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.posted_by = request.user
            job.status = 'active'
            job.save()
            messages.success(request, f"Job '{job.title}' published successfully!")
            return redirect('employer_dashboard')
    else:
        form = JobForm()

    return render(request, 'jobs/post_job.html', {'form': form, 'company': company})

@login_required
def edit_job_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if not (request.user == job.posted_by or request.user.is_site_admin):
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job listing '{job.title}' updated successfully.")
            return redirect('employer_dashboard')
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/edit_job.html', {'form': form, 'job': job})

@login_required
def toggle_job_status(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if not (request.user == job.posted_by or request.user.is_site_admin):
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard_redirect')

    if job.status == 'active':
        job.status = 'closed'
        messages.info(request, f"Job '{job.title}' marked as Closed.")
    else:
        job.status = 'active'
        messages.success(request, f"Job '{job.title}' republished as Active.")
    job.save()
    return redirect('employer_dashboard')

@login_required
def delete_job_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if not (request.user == job.posted_by or request.user.is_site_admin):
        messages.error(request, "Unauthorized action.")
        return redirect('dashboard_redirect')

    job.delete()
    messages.success(request, "Job listing removed.")
    return redirect('employer_dashboard')

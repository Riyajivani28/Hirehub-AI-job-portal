from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Company
from .forms import CompanyForm
from jobs.models import Job

def company_list_view(request):
    companies = Company.objects.filter(verification_status='approved')
    search_q = request.GET.get('q', '').strip()
    industry_q = request.GET.get('industry', '').strip()

    if search_q:
        companies = companies.filter(name__icontains=search_q)
    if industry_q:
        companies = companies.filter(industry__icontains=industry_q)

    industries = Company.objects.values_list('industry', flat=True).distinct()

    return render(request, 'companies/company_list.html', {
        'companies': companies,
        'search_q': search_q,
        'industry_q': industry_q,
        'industries': industries
    })

def company_detail_view(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    active_jobs = Job.objects.filter(company=company, status='active')

    return render(request, 'companies/company_detail.html', {
        'company': company,
        'active_jobs': active_jobs
    })

@login_required
def company_edit_view(request):
    if not request.user.is_employer:
        messages.error(request, "Only Employers can manage company profiles.")
        return redirect('dashboard_redirect')

    company = Company.objects.filter(employer=request.user).first()

    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            c = form.save(commit=False)
            c.employer = request.user
            c.save()
            messages.success(request, "Company profile saved successfully!")
            return redirect('company_detail', company_id=c.id)
    else:
        form = CompanyForm(instance=company)

    return render(request, 'companies/company_edit.html', {
        'form': form,
        'company': company
    })

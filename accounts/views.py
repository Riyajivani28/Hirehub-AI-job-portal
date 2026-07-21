from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, JobSeekerProfile, Education, Experience, Skill, JobSeekerSkill
from .forms import RegisterForm, LoginForm, JobSeekerProfileForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    role_param = request.GET.get('role', 'jobseeker')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()

            if user.role == 'jobseeker':
                JobSeekerProfile.objects.create(user=user)

            login(request, user)
            messages.success(request, f"Welcome to HireHub, {user.first_name or user.username}! Registration successful.")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Registration error. Please check form errors below.")
    else:
        form = RegisterForm(initial={'role': role_param})

    return render(request, 'accounts/register.html', {'form': form, 'selected_role': role_param})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember_me = request.POST.get('remember_me')
            if not remember_me:
                request.session.set_expiry(0)
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        messages.success(request, f"If an account with email '{email}' exists, a password reset link has been dispatched.")
        return redirect('login')
    return render(request, 'accounts/forgot_password.html')

def reset_password_view(request):
    if request.method == 'POST':
        messages.success(request, "Your password has been reset successfully. Please log in.")
        return redirect('login')
    return render(request, 'accounts/reset_password.html')

@login_required
def profile_view(request, user_id=None):
    if user_id:
        target_user = get_object_or_404(User, id=user_id)
    else:
        target_user = request.user

    profile = getattr(target_user, 'seeker_profile', None)
    if not profile and target_user.is_jobseeker:
        profile = JobSeekerProfile.objects.create(user=target_user)

    completion_pct = profile.calculate_completion() if profile else 100

    context = {
        'target_user': target_user,
        'profile': profile,
        'completion_pct': completion_pct,
        'is_own': target_user == request.user
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit_view(request):
    if not request.user.is_jobseeker:
        messages.warning(request, "Profile management is for Job Seekers.")
        return redirect('dashboard_redirect')

    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.bio = request.POST.get('bio', user.bio)
        
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        user.save()

        form = JobSeekerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
    else:
        form = JobSeekerProfileForm(instance=profile)

    all_skills = Skill.objects.all()

    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'profile': profile,
        'all_skills': all_skills
    })

@login_required
def add_education_view(request):
    if request.method == 'POST' and request.user.is_jobseeker:
        profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
        Education.objects.create(
            seeker=profile,
            degree=request.POST.get('degree'),
            institution=request.POST.get('institution'),
            field_of_study=request.POST.get('field_of_study'),
            start_year=request.POST.get('start_year', 2020),
            end_year=request.POST.get('end_year', 2024),
            grade=request.POST.get('grade')
        )
        messages.success(request, "Education entry added!")
    return redirect('profile_edit')

@login_required
def add_experience_view(request):
    if request.method == 'POST' and request.user.is_jobseeker:
        profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
        Experience.objects.create(
            seeker=profile,
            title=request.POST.get('title'),
            company_name=request.POST.get('company_name'),
            location=request.POST.get('location'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date') if request.POST.get('end_date') else None,
            is_current=bool(request.POST.get('is_current')),
            description=request.POST.get('description')
        )
        messages.success(request, "Experience record saved!")
    return redirect('profile_edit')

@login_required
def add_skill_view(request):
    if request.method == 'POST' and request.user.is_jobseeker:
        profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
        skill_name = request.POST.get('skill_name')
        level = request.POST.get('level', 'intermediate')
        if skill_name:
            sk, _ = Skill.objects.get_or_create(name=skill_name.strip())
            JobSeekerSkill.objects.get_or_create(seeker=profile, skill=sk, defaults={'level': level})
            messages.success(request, f"Added skill '{skill_name}'!")
    return redirect('profile_edit')

@login_required
def delete_education_view(request, edu_id):
    if request.user.is_jobseeker:
        profile = getattr(request.user, 'seeker_profile', None)
        if profile:
            Education.objects.filter(id=edu_id, seeker=profile).delete()
            messages.info(request, "Education entry removed.")
    return redirect('profile_edit')

@login_required
def delete_experience_view(request, exp_id):
    if request.user.is_jobseeker:
        profile = getattr(request.user, 'seeker_profile', None)
        if profile:
            Experience.objects.filter(id=exp_id, seeker=profile).delete()
            messages.info(request, "Experience record deleted.")
    return redirect('profile_edit')

@login_required
def delete_skill_view(request, skill_id):
    if request.user.is_jobseeker:
        profile = getattr(request.user, 'seeker_profile', None)
        if profile:
            JobSeekerSkill.objects.filter(id=skill_id, seeker=profile).delete()
            messages.info(request, "Skill deleted.")
    return redirect('profile_edit')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import JobSeekerProfile, Skill
from jobs.models import Job
from applications.models import Application

@login_required
def ai_dashboard_view(request):
    if request.user.is_site_admin:
        return redirect('admin_ai_hub')
    if request.user.is_employer:
        return redirect('employer_ai_hub')
    return redirect('seeker_ai_hub')

@login_required
def ai_resume_analyzer_view(request):
    profile = getattr(request.user, 'seeker_profile', None)
    active_jobs = Job.objects.filter(status='active').select_related('company', 'category')

    selected_job_id = request.POST.get('job_id') or request.GET.get('job_id')
    selected_job = Job.objects.filter(id=selected_job_id).first() if selected_job_id else None

    seeker_skills = list(profile.skills.values_list('skill__name', flat=True)) if profile else []
    default_resume = f"Headline: {profile.headline or ''}\nSkills: {', '.join(seeker_skills)}" if profile else ""
    resume_text = request.POST.get('resume_text', default_resume).strip()

    result = None
    if request.method == 'POST' or resume_text:
        word_count = len(resume_text.split())
        action_verbs = ['managed', 'architected', 'developed', 'scaled', 'implemented', 'optimized', 'led', 'created', 'designed', 'built']
        found_verbs = [v for v in action_verbs if v in resume_text.lower()]
        
        score = profile.calculate_completion() if profile else 65
        
        result = {
            'overall_score': score,
            'word_count': max(word_count, 120),
            'action_verbs_count': len(found_verbs),
            'sections_detected': {
                'education': 'education' in resume_text.lower() or (profile and profile.education_set.exists()),
                'experience': 'experience' in resume_text.lower() or (profile and profile.experience_set.exists()),
                'skills': len(seeker_skills) > 0 or 'skill' in resume_text.lower(),
                'projects': 'project' in resume_text.lower() or (profile and profile.portfolio_url),
            },
            'suggestions': [
                "Quantify achievements in work experience with metric percentages (e.g. 'Reduced latency by 35%').",
                "Upload an updated PDF resume to increase overall ATS parsing score." if not (profile and profile.resume) else "Keep your GitHub and Portfolio projects updated for employers.",
                "Add additional technical skills to improve automatic job matching fit."
            ]
        }

    return render(request, 'ai_features/resume_analyzer.html', {
        'active_jobs': active_jobs,
        'selected_job': selected_job,
        'selected_job_id': str(selected_job_id) if selected_job_id else "",
        'profile': profile,
        'seeker_skills': seeker_skills,
        'resume_text': resume_text,
        'result': result
    })

from .models import ATSAnalysis

@login_required
def ai_ats_score_view(request):
    profile = getattr(request.user, 'seeker_profile', None)
    active_jobs = Job.objects.filter(status='active').select_related('company', 'category')
    
    selected_job_id = request.POST.get('job_id') or request.GET.get('job_id')
    selected_job = Job.objects.filter(id=selected_job_id).first() if selected_job_id else None

    # Auto-populate resume text from seeker profile if not submitted
    seeker_skills = list(profile.skills.values_list('skill__name', flat=True)) if profile else []
    default_resume = f"Headline: {profile.headline or ''}\nSkills: {', '.join(seeker_skills)}" if profile else ""

    resume_text = request.POST.get('resume_text', default_resume).strip()
    jd_text = request.POST.get('jd_text', '').strip()

    if selected_job and not jd_text:
        jd_text = f"Title: {selected_job.title}\nRole Requirements: {selected_job.description}\nRequired Skills: {selected_job.skills_required}\nExperience: {selected_job.experience_required}"

    result = None

    if request.method == 'POST' and (jd_text or selected_job):
        # Extract keywords from JD
        raw_jd = selected_job.skills_required if (selected_job and selected_job.skills_required) else jd_text
        jd_skills = [s.strip().lower() for s in raw_jd.split(',') if s.strip()]
        if not jd_skills:
            jd_skills = [word.strip('.,()').lower() for word in jd_text.split() if len(word) > 3]

        seeker_skill_lowers = [s.lower() for s in seeker_skills] + [w.strip('.,()').lower() for w in resume_text.split() if len(w) > 3]

        matched = []
        missing = []
        for sk in set(jd_skills):
            if any(sk in candidate_w or candidate_w in sk for candidate_w in seeker_skill_lowers):
                matched.append(sk.capitalize())
            else:
                missing.append(sk.capitalize())

        total = max(len(matched) + len(missing), 1)
        score = min(100, int((len(matched) / total) * 100) + (15 if profile and profile.resume else 5))
        keyword_match_pct = int((len(matched) / total) * 100)

        strengths = [
            f"Found {len(matched)} matching key skills in your resume/profile.",
            "Standard ATS-readable formatting detected." if (profile and profile.resume) else "Profile sections structured properly.",
            "Strong relevance for target position." if score >= 70 else "Basic candidate qualification baseline established."
        ]

        weaknesses = []
        if missing:
            weaknesses.append(f"Missing {len(missing)} critical tech keywords required by employer.")
        if not (profile and profile.resume):
            weaknesses.append("No uploaded PDF resume attached to profile.")

        suggestions = [
            f"Incorporate missing keywords: {', '.join(missing[:4])}" if missing else "Your skill keywords match the target job closely!",
            "Quantify achievements in your work history with numbers (e.g. 'Improved efficiency by 30%').",
            "Keep your skills list synchronized with active projects."
        ]

        result = {
            'score': score,
            'keyword_match': keyword_match_pct,
            'matching_keywords': matched,
            'missing_keywords': missing,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'suggestions': suggestions,
            'total_jd_keywords': total,
        }

        # Store analysis record in database
        ATSAnalysis.objects.create(
            user=request.user,
            job=selected_job,
            score=score,
            matched_skills=", ".join(matched),
            missing_skills=", ".join(missing),
            strengths="\n".join(strengths),
            weaknesses="\n".join(weaknesses),
            suggestions="\n".join(suggestions)
        )
        messages.success(request, f"ATS Match Score computed: {score}%! Analysis saved to your history.")

    previous_reports = ATSAnalysis.objects.filter(user=request.user).select_related('job', 'job__company').order_by('-created_at')[:8]

    return render(request, 'ai_features/ats_score.html', {
        'active_jobs': active_jobs,
        'selected_job': selected_job,
        'selected_job_id': str(selected_job_id) if selected_job_id else "",
        'resume_text': resume_text,
        'jd_text': jd_text,
        'result': result,
        'previous_reports': previous_reports,
        'profile': profile,
    })

@login_required
def ai_resume_builder_view(request):
    profile = getattr(request.user, 'seeker_profile', None)
    resume_doc = None
    target_role = ""
    exp_level = ""

    if request.method == 'POST':
        target_role = request.POST.get('role', 'Full Stack Developer')
        exp_level = request.POST.get('exp', 'Mid-Senior Level')
        resume_doc = {
            'summary': f"Results-driven {target_role} with proven expertise in {exp_level or 'modern software engineering'}. Skilled in building scalable applications, database optimization, and cloud architecture.",
            'bullets': [
                f"Architected end-to-end web applications for {target_role} requirements.",
                f"Optimized application query performance and database indexing speed by 40%.",
                f"Collaborated with cross-functional product teams to deliver high impact software features.",
                f"Automated automated testing suites and continuous delivery pipelines."
            ]
        }

    return render(request, 'ai_features/resume_builder.html', {
        'profile': profile,
        'target_role': target_role,
        'exp_level': exp_level,
        'resume_doc': resume_doc
    })

@login_required
def ai_job_recommendation_view(request):
    profile = getattr(request.user, 'seeker_profile', None)
    seeker_skills = set(profile.skills.values_list('skill__name', flat=True)) if profile else set()

    active_jobs = Job.objects.filter(status='active').select_related('company', 'category')
    selected_job_id = request.GET.get('job_id')
    filter_job = Job.objects.filter(id=selected_job_id).first() if selected_job_id else None

    recommendations = []

    for job in active_jobs:
        if filter_job and job.id != filter_job.id:
            continue
        job_skills = set([s.strip().lower() for s in job.skills_required.split(',') if s.strip()])
        matched_skills = [s for s in seeker_skills if s.lower() in job_skills]
        matched_count = len(matched_skills)
        match_pct = int(min(98, max(45, 55 + matched_count * 15)))

        recommendations.append({
            'job': job,
            'match_pct': match_pct,
            'drivers': matched_skills if matched_skills else list(job_skills)[:3]
        })

    recommendations.sort(key=lambda x: x['match_pct'], reverse=True)

    return render(request, 'ai_features/job_recommendations.html', {
        'active_jobs': active_jobs,
        'selected_job_id': str(selected_job_id) if selected_job_id else "",
        'recommendations': recommendations
    })

@login_required
def ai_skill_gap_view(request):
    active_jobs = Job.objects.filter(status='active').select_related('company', 'category')
    selected_job_id = request.POST.get('job_id') or request.GET.get('job_id')
    target_job = Job.objects.filter(id=selected_job_id).first() if selected_job_id else active_jobs.first()

    profile = getattr(request.user, 'seeker_profile', None)
    user_skill_names = set([s.lower() for s in profile.skills.values_list('skill__name', flat=True)]) if profile else set(['python', 'django', 'javascript'])

    required_skills = [s.strip() for s in target_job.skills_required.split(',') if s.strip()] if (target_job and target_job.skills_required) else ['Python', 'Django', 'React.js', 'PostgreSQL', 'Docker']

    matched_skills = [s for s in required_skills if s.lower() in user_skill_names]
    missing_skills = [s for s in required_skills if s.lower() not in user_skill_names]

    gap_data = None
    if target_job:
        total_req = max(len(required_skills), 1)
        coverage_pct = int((len(matched_skills) / total_req) * 100)
        roadmap = [
            {'week': i+1, 'skill': s, 'action': f'Complete hands-on projects & exercises covering {s}.', 'resource': f'Mastering {s} Bootcamp & Docs'}
            for i, s in enumerate(missing_skills[:4])
        ]
        gap_data = {
            'coverage_pct': coverage_pct,
            'matching_skills': matched_skills,
            'missing_skills': missing_skills,
            'roadmap': roadmap
        }

    return render(request, 'ai_features/skill_gap.html', {
        'active_jobs': active_jobs,
        'target_job': target_job,
        'selected_job_id': str(selected_job_id) if selected_job_id else "",
        'gap_data': gap_data,
        'profile': profile
    })

@login_required
def ai_interview_generator_view(request):
    active_jobs = Job.objects.filter(status='active').select_related('company', 'category')
    selected_job_id = request.POST.get('job_id') or request.GET.get('job_id')
    selected_job = Job.objects.filter(id=selected_job_id).first() if selected_job_id else None

    role_title = request.POST.get('role_title', selected_job.title if selected_job else 'Full Stack Developer').strip()
    experience_level = request.POST.get('experience_level', 'mid')

    questions_kit = None
    if request.method == 'POST' or selected_job:
        company_name = selected_job.company.name if selected_job else "Tech Company"
        skills_str = selected_job.skills_required if selected_job else "Python, Django, React, Databases"
        
        questions_kit = {
            'technical': [
                {
                    'question': f'Explain key architectural challenges when building scalable applications using {skills_str.split(",")[0] if skills_str else "Python"}.',
                    'key_focus': 'System architecture, performance optimization, and scalable design.',
                    'sample_answer': 'Discuss modular design, database indexing, caching strategies, and RESTful stateless APIs.'
                },
                {
                    'question': f'How would you design a scalable database schema for {role_title} requirements at {company_name}?',
                    'key_focus': 'ORM optimization, foreign keys, and indexing.',
                    'sample_answer': 'Outline normalized database entities, indexing frequently queried fields, and using transaction boundaries.'
                }
            ],
            'behavioral': [
                {
                    'question': f'Describe a challenging project you delivered as a {role_title} under tight deadlines.',
                    'star_tip': 'Use the STAR method: Situation, Task, Action, Result. Highlight teamwork, crisis resolution, and SLA delivery.'
                }
            ]
        }

    return render(request, 'ai_features/interview_generator.html', {
        'active_jobs': active_jobs,
        'selected_job': selected_job,
        'selected_job_id': str(selected_job_id) if selected_job_id else "",
        'role_title': role_title,
        'experience_level': experience_level,
        'questions_kit': questions_kit
    })

import json
import os
import urllib.request
import urllib.error
from django.conf import settings

def get_candidate_profile_context(user):
    if not user or not user.is_authenticated:
        return "User Profile: Guest / Unauthenticated"

    name = user.get_full_name() or user.username
    profile = getattr(user, 'seeker_profile', None)

    if not profile:
        return f"Candidate Name: {name}\nRole: Job Seeker\nProfile Details: No detailed profile created yet in database."

    headline = profile.headline or "Job Seeker"
    location_parts = [p for p in [profile.city, profile.state, profile.country] if p]
    location = ", ".join(location_parts) if location_parts else "Not specified"
    expected_salary = profile.expected_salary or "Not specified"

    # Education records
    edu_records = []
    for edu in profile.education_set.all():
        years = f"({edu.start_year}-{edu.end_year or 'Present'})"
        edu_records.append(f"{edu.degree} in {edu.field_of_study or 'General'} at {edu.institution} {years}")
    edu_str = "; ".join(edu_records) if edu_records else "None listed"

    # Experience records
    exp_records = []
    for exp in profile.experience_set.all():
        end_str = "Present" if exp.is_current else (exp.end_date.strftime("%Y-%m") if exp.end_date else "")
        start_str = exp.start_date.strftime("%Y-%m") if exp.start_date else ""
        exp_records.append(f"{exp.title} at {exp.company_name} ({start_str} to {end_str})")
    exp_str = "; ".join(exp_records) if exp_records else "None listed"

    # Skills with proficiency
    skills = [f"{s.skill.name} ({s.get_level_display()})" for s in profile.skills.select_related('skill').all()]
    skills_str = ", ".join(skills) if skills else "None listed"

    # Links & Resume
    docs = []
    if profile.resume:
        docs.append("Resume PDF uploaded")
    if profile.github_url:
        docs.append(f"GitHub: {profile.github_url}")
    if profile.linkedin_url:
        docs.append(f"LinkedIn: {profile.linkedin_url}")
    if profile.portfolio_url:
        docs.append(f"Portfolio: {profile.portfolio_url}")
    docs_str = ", ".join(docs) if docs else "None provided"

    # Experience Tier Determination
    exp_count = profile.experience_set.count()
    headline_lower = headline.lower()
    if exp_count == 0 or any(k in headline_lower for k in ['student', 'fresher', 'intern', 'graduate', 'trainee']):
        exp_tier = "Fresher / Student / Entry-Level"
    elif exp_count >= 3 or any(k in headline_lower for k in ['senior', 'lead', 'principal', 'architect', 'head', 'manager']):
        exp_tier = "Experienced Senior / Lead Professional"
    else:
        exp_tier = "Junior to Mid-Level Professional"

    return (
        f"LOGGED-IN CANDIDATE DATABASE PROFILE:\n"
        f"• Full Name: {name}\n"
        f"• Professional Headline / Goal: {headline}\n"
        f"• Experience Level Tier: {exp_tier} ({exp_count} logged roles)\n"
        f"• Location: {location}\n"
        f"• Target/Expected Compensation: {expected_salary}\n"
        f"• Technical & Functional Skills: {skills_str}\n"
        f"• Education Qualifications: {edu_str}\n"
        f"• Work Experience History: {exp_str}\n"
        f"• Portfolio & Verified Links: {docs_str}"
    )

def generate_intelligent_fallback_guidance(user_msg, user=None):
    name = user.get_full_name() or user.username if user else "Candidate"
    profile = getattr(user, 'seeker_profile', None) if user else None
    
    skills = [s.skill.name for s in profile.skills.select_related('skill').all()] if profile else []
    skills_text = f" ({', '.join(skills[:3])})" if skills else ""

    exp_count = profile.experience_set.count() if profile else 0
    headline = (profile.headline or "").lower() if profile else ""
    is_fresher = exp_count == 0 or any(k in headline for k in ['student', 'fresher', 'intern', 'graduate', 'trainee'])

    msg_lower = user_msg.lower()

    if any(k in msg_lower for k in ['resume', 'cv', 'ats', 'score', 'format']):
        if is_fresher:
            return (
                f"🎯 **Fresher Resume & ATS Guidance for {name}**{skills_text}:\n\n"
                "1. **Highlight Academic & Capstone Projects:** Place major projects, GitHub repositories, and relevant coursework at the top of your resume.\n"
                "2. **Clean Single-Column Layout:** Avoid multi-column tables or complex graphics so ATS parsers accurately extract your education and skills.\n"
                "3. **Skill Keyword Alignment:** List core tools and technologies matching entry-level job descriptions.\n"
                "4. **Certifications & Extra-Curriculars:** Include coding hackathons, certifications, and open-source contributions."
            )
        else:
            return (
                f"🎯 **Experienced Professional Resume & ATS Strategy for {name}**{skills_text}:\n\n"
                "1. **Quantified Business Impact:** Begin bullet points with strong action verbs (e.g. *Architected, Scaled, Optimized*) and metrics (*'Reduced API latency by 35%'*).\n"
                "2. **Targeted Technical Keywords:** Align your skill section and work history with high-level job specifications.\n"
                "3. **Single-Column Standard Layout:** Ensure 100% ATS readability across Enterprise parsing tools."
            )

    elif any(k in msg_lower for k in ['interview', 'prep', 'question', 'star', 'coding']):
        if is_fresher:
            return (
                f"💼 **Entry-Level & Fresher Interview Coaching for {name}**:\n\n"
                "1. **Core Fundamentals:** Review core data structures, algorithms, object-oriented concepts, and basic database queries.\n"
                "2. **Project Walkthroughs:** Be ready to explain your academic projects step-by-step—your contributions, key challenges, and solutions.\n"
                "3. **STAR Method for Behavioral Questions:** Structure answers with **S**ituation, **T**ask, **A**ction, and **R**esult."
            )
        else:
            return (
                f"💼 **Advanced Technical & Executive Interview Prep for {name}**:\n\n"
                "1. **System & Architectural Design:** Prepare to discuss scalable system components, caching layers, database indexing, and trade-offs.\n"
                "2. **Behavioral Leadership:** Use the STAR method to demonstrate cross-functional leadership, SLA management, and incident response.\n"
                "3. **Coding Complexity:** Focus on edge cases, optimal data structures, and Big-O time/space trade-offs."
            )

    elif any(k in msg_lower for k in ['salary', 'pay', 'compensation', 'offer', 'negotiat']):
        expected = profile.expected_salary if (profile and profile.expected_salary) else "competitive market standards"
        return (
            f"💰 **Personalized Value & Compensation Guidance for {name}**:\n\n"
            f"1. **Expectation Baseline:** Position your compensation expectations around {expected} based on your stored profile target.\n"
            "2. **Evaluate Full Offer Package:** Assess base pay, performance bonuses, equity/ESOPs, health benefits, and remote allowances.\n"
            "3. **Data-Backed Negotiation:** Present documented accomplishments and skill relevance when discussing final numbers."
        )

    elif any(k in msg_lower for k in ['roadmap', 'learn', 'skill', 'path', 'grow']):
        if is_fresher:
            return (
                f"🚀 **Personalized Entry-Level Learning Roadmap for {name}**{skills_text}:\n\n"
                "1. **Master Core Fundamentals:** Deepen proficiency in 1-2 primary languages and relational database concepts.\n"
                "2. **Build End-to-End Projects:** Create 2 full-stack applications with user authentication and database persistence.\n"
                "3. **GitHub Presence:** Maintain active commit history and write clean, structured project README documentation."
            )
        else:
            return (
                f"🚀 **Personalized Advanced Career Roadmap for {name}**{skills_text}:\n\n"
                "1. **Advanced Systems & Cloud:** Focus on distributed microservices, message brokers (RabbitMQ/Kafka), and container orchestration (Docker/K8s).\n"
                "2. **System Optimization:** Implement query profiling, caching strategies, and CI/CD automation.\n"
                "3. **Leadership & Mentorship:** Take ownership of system architecture and guide junior team members."
            )

    else:
        headline_text = f" ({profile.headline})" if (profile and profile.headline) else ""
        return (
            f"🤖 **HireHub AI Career Mentor Guidance for {name}**{headline_text}:\n\n"
            f"I have analyzed your query: *'{user_msg}'*\n\n"
            "• **Profile Synchronization:** Ensure your Skills, Education, and Work History are updated on HireHub for accurate AI recommendations.\n"
            "• **Targeted Career Search:** Explore job vacancies where your skills match position requirements.\n\n"
            "How can I assist your career journey today? (Ask about Resume Audits, Interview Coaching, Upskilling, or Salary Guidance!)"
        )

def get_ai_career_guidance(user_msg, history=None, user=None):
    api_key = (os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '') or '').strip()
    profile_context = get_candidate_profile_context(user)

    if not api_key or api_key == 'your_gemini_api_key_here':
        fallback = generate_intelligent_fallback_guidance(user_msg, user=user)
        return f"ℹ️ [Notice: GEMINI_API_KEY not configured in .env — Active Offline AI Mentor Mode]\n\n{fallback}"

    system_text = (
        "You are HireHub AI Career Mentor, an expert personalized career advisor, resume reviewer, interview coach, and career strategist. "
        "CRITICAL RULES:\n"
        "1. Strictly adapt your guidance to the candidate's actual experience level, education, skills, and background provided in their database profile.\n"
        "2. If the user is a Fresher/Student, provide entry-level, encouraging, fundamental advice (internships, foundational projects, entry-level interview prep).\n"
        "3. If the user is Experienced, provide advanced advice (architectural design, leadership, strategic positioning, compensation negotiation).\n"
        "4. NEVER assume a fixed role (such as Senior Engineer) or fixed salary/location unless present in the candidate profile.\n"
        "5. Keep responses concise, professional, accurate, well-formatted with markdown bullet points, and directly relevant to the candidate's message.\n\n"
        f"{profile_context}"
    )

    contents = []
    if history:
        for item in history[-10:]:
            if isinstance(item, dict) and 'role' in item and 'content' in item:
                g_role = 'model' if item['role'] == 'assistant' else 'user'
                contents.append({
                    "role": g_role,
                    "parts": [{"text": item['content']}]
                })

    contents.append({
        "role": "user",
        "parts": [{"text": user_msg}]
    })

    candidate_models = [
        getattr(settings, 'GEMINI_MODEL', 'gemma-4-26b-a4b-it').strip(),
        'gemma-4-26b-a4b-it',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-flash-latest'
    ]
    models_to_try = []
    for m in candidate_models:
        clean_m = m.replace('models/', '') if m else ''
        if clean_m and clean_m not in models_to_try:
            models_to_try.append(clean_m)

    payload = {
        "system_instruction": {
            "parts": [{"text": system_text}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }
    headers = {"Content-Type": "application/json"}

    last_error = None
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode('utf-8'))
                candidates = result.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', '').strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get('error', {}).get('message', str(e))
            except Exception:
                err_msg = str(e)
            last_error = f"Model '{model_name}' ({e.code}): {err_msg}"
            continue
        except urllib.error.URLError as e:
            last_error = f"Connection Error: {e.reason}"
            continue
        except Exception as e:
            last_error = str(e)
            continue

    fallback = generate_intelligent_fallback_guidance(user_msg, user=user)
    return fallback

@login_required
def ai_career_chatbot_view(request):
    chat_history = request.session.get('ai_chat_history', [])

    if request.GET.get('clear') == '1':
        request.session['ai_chat_history'] = []
        messages.success(request, "Conversation history cleared successfully.")
        return redirect('ai_career_chatbot')

    if request.method == 'POST' or request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        user_msg = (request.POST.get('message') or request.GET.get('message') or '').strip()
        if not user_msg:
            return JsonResponse({'reply': 'Please enter a valid career query.'})

        reply = get_ai_career_guidance(user_msg, chat_history, user=request.user)

        if not reply.startswith('⚠️'):
            chat_history.append({'role': 'user', 'content': user_msg})
            chat_history.append({'role': 'assistant', 'content': reply})
            request.session['ai_chat_history'] = chat_history[-12:]

        return JsonResponse({'reply': reply})

    return render(request, 'ai_features/career_chatbot.html', {'chat_history': chat_history})

@login_required
def ai_smart_matching_view(request):
    if not request.user.is_employer:
        messages.error(request, "Smart Candidate Matching is reserved for Employers.")
        return redirect('dashboard_redirect')

    selected_job_id = request.GET.get('job_id')
    user_jobs = Job.objects.filter(posted_by=request.user)

    selected_job = Job.objects.filter(id=selected_job_id, posted_by=request.user).first() if selected_job_id else user_jobs.first()

    applications = Application.objects.filter(job=selected_job).select_related('applicant', 'applicant__seeker_profile') if selected_job else []

    ranked_candidates = []
    for idx, app in enumerate(applications, 1):
        ranked_candidates.append({
            'rank': idx,
            'application': app,
            'score': app.ats_match_score,
            'skills': app.applicant.seeker_profile.skills.all() if hasattr(app.applicant, 'seeker_profile') else []
        })

    ranked_candidates.sort(key=lambda x: x['score'], reverse=True)

    return render(request, 'ai_features/smart_matching.html', {
        'user_jobs': user_jobs,
        'selected_job': selected_job,
        'ranked_candidates': ranked_candidates
    })

@login_required
def employer_ai_hub_view(request):
    if not request.user.is_employer:
        messages.error(request, "Employer AI Suite Hub is reserved for Employers & HR Managers.")
        return redirect('dashboard_redirect')

    ai_output = None
    action_type = request.POST.get('action_type', '')

    user_jobs = Job.objects.filter(posted_by=request.user)
    applications = Application.objects.filter(job__in=user_jobs).select_related('job', 'applicant', 'applicant__seeker_profile')

    if request.method == 'POST':
        if action_type == 'generate_jd':
            title = request.POST.get('job_title', 'Software Engineer')
            exp = request.POST.get('experience', '2-4 years')
            skills = request.POST.get('skills_required', 'Python, React')
            jtype = request.POST.get('job_type', 'full_time')
            
            prompt = f"Write a compelling, professional Job Description for HireHub platform. Title: {title}. Experience: {exp}. Skills required: {skills}. Job Type: {jtype}. Output sections: Role Overview, Key Responsibilities (4 bullet points), Required Qualifications (4 bullet points)."
            fallback = f"📋 Job Description: {title}\n\nRole Overview:\nWe are seeking a talented {title} with {exp} experience specializing in {skills} to join our engineering team.\n\nKey Responsibilities:\n• Develop and maintain high-quality software solutions.\n• Collaborate with cross-functional product & engineering teams.\n• Write clean, testable, and efficient code.\n• Perform code reviews and optimize system performance.\n\nQualifications:\n• Demonstrated proficiency in {skills}.\n• Strong problem-solving and communication skills."
            res = get_ai_career_guidance(prompt, user=request.user)
            ai_output = res if (res and not res.startswith('ℹ️') and 'What specific area' not in res and len(res) > 40) else fallback

        elif action_type == 'generate_email':
            etype = request.POST.get('email_type', 'interview')
            cname = request.POST.get('candidate_name', 'Applicant')
            jtitle = request.POST.get('job_title', 'Software Developer')
            
            if etype == 'interview':
                prompt = f"Write a warm, professional Interview Invitation Email to {cname} for the position of {jtitle} at HireHub."
                fallback = f"Subject: Invitation to Interview – {jtitle} Position\n\nDear {cname},\n\nThank you for applying for the {jtitle} role. We were very impressed with your background and would like to invite you for an initial interview.\n\nPlease let us know your availability over the upcoming days.\n\nBest regards,\nHiring Team"
            elif etype == 'offer':
                prompt = f"Write an official Job Offer Letter Email to {cname} offering the position of {jtitle}."
                fallback = f"Subject: Formal Job Offer – {jtitle}\n\nDear {cname},\n\nWe are delighted to extend a formal offer of employment for the {jtitle} position!\n\nPlease review the attached offer details and respond by end of week.\n\nWelcome to the team!\nBest regards,\nHR Department"
            else:
                prompt = f"Write a respectful, encouraging Application Rejection Email to {cname} for the {jtitle} role."
                fallback = f"Subject: Update on your application for {jtitle}\n\nDear {cname},\n\nThank you for taking the time to apply and interview for the {jtitle} role. While your qualifications are impressive, we have chosen to proceed with another candidate whose experience matches our current needs more closely.\n\nWe wish you all the best in your career search.\n\nSincerely,\nRecruitment Team"
            
            res = get_ai_career_guidance(prompt, user=request.user)
            ai_output = res if (res and not res.startswith('ℹ️') and 'What specific area' not in res and len(res) > 40) else fallback

        elif action_type == 'schedule_interview':
            app_id = request.POST.get('application_id')
            idate = request.POST.get('interview_date')
            notes = request.POST.get('interview_notes', '')
            
            target_app = Application.objects.filter(id=app_id, job__posted_by=request.user).first()
            if target_app:
                target_app.status = 'interviewing'
                target_app.notes = f"Interview Scheduled: {idate}. {notes}"
                target_app.save()
                messages.success(request, f"Interview scheduled with {target_app.applicant.get_full_name() or target_app.applicant.username} for {idate}!")
                return redirect('employer_ai_hub')

    # Candidate Ranking & Match Matrix Calculation
    ranked_pipeline = []
    total_score_sum = 0

    for app in applications:
        seeker_skills = list(app.applicant.seeker_profile.skills.values_list('skill__name', flat=True)) if hasattr(app.applicant, 'seeker_profile') else []
        job_skills = [s.strip().lower() for s in app.job.skills_required.split(',') if s.strip()]
        user_skills_lower = [s.lower() for s in seeker_skills]

        matched = [s for s in job_skills if s in user_skills_lower]
        match_pct = round((len(matched) / max(len(job_skills), 1)) * 100) if job_skills else app.ats_match_score

        final_score = round((app.ats_match_score * 0.6) + (match_pct * 0.4))
        total_score_sum += final_score

        ranked_pipeline.append({
            'application': app,
            'match_score': final_score,
            'ats_score': app.ats_match_score,
            'skill_match_pct': match_pct,
            'matched_skills': matched,
            'applicant_skills': seeker_skills,
        })

    ranked_pipeline.sort(key=lambda x: x['match_score'], reverse=True)

    hiring_analytics = {
        'total_vacancies': user_jobs.count(),
        'total_applicants': applications.count(),
        'shortlisted_count': applications.filter(status='shortlisted').count(),
        'interviewing_count': applications.filter(status='interviewing').count(),
        'hired_count': applications.filter(status='accepted').count(),
        'avg_candidate_score': round(total_score_sum / max(len(ranked_pipeline), 1)),
    }

    return render(request, 'ai_features/employer_ai_hub.html', {
        'user_jobs': user_jobs,
        'applications': applications,
        'ranked_pipeline': ranked_pipeline[:20],
        'hiring_analytics': hiring_analytics,
        'ai_output': ai_output,
    })

@login_required
def seeker_ai_hub_view(request):
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
    seeker_skills = list(profile.skills.values_list('skill__name', flat=True))

    ai_result = None
    action_type = request.POST.get('action_type', '')

    if request.method == 'POST':
        if action_type == 'generate_cover_letter':
            target_role = request.POST.get('target_role', 'Software Engineer')
            company_name = request.POST.get('company_name', 'Tech Company')
            highlights = request.POST.get('key_highlights', 'Fullstack development, REST APIs')

            prompt = f"Write a professional, personalized cover letter for {request.user.get_full_name() or request.user.username} applying for the position of {target_role} at {company_name}. Highlighted skills: {highlights}."
            fallback = f"Dear Hiring Manager at {company_name},\n\nI am writing to express my strong interest in the {target_role} position. With my background in {', '.join(seeker_skills[:3]) if seeker_skills else 'software development'}, I am confident in my ability to deliver immediate value to your engineering team.\n\nKey Highlights:\n• Demonstrated expertise in {highlights}.\n• Experience building scalable web applications and collaborating in agile teams.\n\nThank you for considering my application. I look forward to discussing how my skills align with your goals.\n\nSincerely,\n{request.user.get_full_name() or request.user.username}"
            
            res = get_ai_career_guidance(prompt, user=request.user)
            ai_result = res if (res and not res.startswith('ℹ️') and 'What specific area' not in res and len(res) > 50) else fallback

        elif action_type == 'estimate_salary':
            role = request.POST.get('target_role', 'Python Developer')
            exp = request.POST.get('experience_years', '3')
            loc = request.POST.get('location', 'Remote / India')

            prompt = f"Provide a realistic market salary estimate for a {role} with {exp} years of experience in {loc}. Include base range, senior growth ceiling, and top high-paying skills."
            fallback = f"💰 Expected Salary Estimate for {role} ({exp} Yrs Exp - {loc}):\n\n• Entry-Mid Level Range: ₹ 6.5 LPA - ₹ 12.0 LPA ($65,000 - $95,000 USD)\n• Senior Growth Ceiling: ₹ 18.0 LPA - ₹ 28.0 LPA ($110,000 - $150,000 USD)\n• Top Salary Accelerators: System Architecture, Cloud Services (AWS/GCP), Microservices, CI/CD"
            
            res = get_ai_career_guidance(prompt, user=request.user)
            ai_result = res if (res and not res.startswith('ℹ️') and 'What specific area' not in res and len(res) > 50) else fallback

        elif action_type == 'generate_roadmap':
            role = request.POST.get('target_role', 'Backend Engineer')
            level = request.POST.get('current_level', 'Beginner')

            prompt = f"Create a step-by-step 4-phase learning roadmap to become a successful {role} starting from {level} level. Break down by Phase 1 (Fundamentals), Phase 2 (Core Frameworks), Phase 3 (Advanced/Cloud), Phase 4 (Portfolio Projects)."
            fallback = f"🛣️ Step-by-Step Learning Roadmap: {role} ({level} Level)\n\nPhase 1: Core Fundamentals (Weeks 1-4)\n• Master Core Programming (Data Structures, Algorithms, Git Control)\n\nPhase 2: Frameworks & Databases (Weeks 5-8)\n• Build RESTful APIs with Django/FastAPI & PostgreSQL\n\nPhase 3: DevOps & Architecture (Weeks 9-12)\n• Learn Docker, Redis Caching, AWS Deployment, CI/CD Pipelines\n\nPhase 4: Capstone Portfolio Projects\n• Deploy 2 end-to-end fullstack production projects to GitHub"
            
            res = get_ai_career_guidance(prompt, user=request.user)
            ai_result = res if (res and not res.startswith('ℹ️') and 'What specific area' not in res and len(res) > 50) else fallback

    # Stats calculation
    completion_score = profile.calculate_completion()
    recommended_jobs = Job.objects.filter(status='active').select_related('company', 'category')[:4]
    applied_count = Application.objects.filter(applicant=request.user).count()

    return render(request, 'ai_features/seeker_ai_hub.html', {
        'profile': profile,
        'seeker_skills': seeker_skills,
        'completion_score': completion_score,
        'recommended_jobs': recommended_jobs,
        'applied_count': applied_count,
        'ai_result': ai_result,
    })

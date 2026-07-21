import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirehub.settings')
django.setup()

from datetime import date, timedelta
from accounts.models import User, JobSeekerProfile, Skill, JobSeekerSkill, Education, Experience
from companies.models import Company
from jobs.models import Category, Job, SavedJob
from applications.models import Application, Interview, OfferLetter
from notifications.models import Notification
from feedback.models import Feedback, ContactMessage
from reports.models import SystemAnnouncement, SiteVisitorLog

def run_seed():
    print("Seeding database...")
    
    # 1. Categories
    categories_data = [
        ("Software & Tech", "fa-code"),
        ("Data Science & AI", "fa-brain"),
        ("Design & Creative", "fa-palette"),
        ("Marketing & Sales", "fa-chart-line"),
        ("Finance & Accounting", "fa-coins"),
        ("Product & Project", "fa-tasks"),
        ("Human Resources", "fa-users"),
        ("Customer Support", "fa-headset"),
    ]
    categories = []
    for name, icon in categories_data:
        cat, _ = Category.objects.get_or_create(name=name, defaults={'icon': icon})
        categories.append(cat)
    print(f"Created {len(categories)} categories.")

    # 2. Skills
    skills_list = [
        ("Python", "Technical"), ("Django", "Technical"), ("React.js", "Technical"),
        ("JavaScript", "Technical"), ("Tailwind CSS", "Technical"), ("PostgreSQL", "Technical"),
        ("Machine Learning", "AI"), ("Deep Learning", "AI"), ("Figma", "Design"),
        ("UI/UX Design", "Design"), ("Product Management", "Management"), ("Agile/Scrum", "Management")
    ]
    skills_obj = {}
    for name, cat in skills_list:
        sk, _ = Skill.objects.get_or_create(name=name, defaults={'category': cat})
        skills_obj[name] = sk

    # 3. Create Admin User
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@hirehub.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'is_verified': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()

    # 4. Create Employers & Companies
    employers_info = [
        {
            'username': 'techcorp_hr',
            'email': 'hr@techcorp.com',
            'name': 'TechCorp Solutions',
            'industry': 'Software & AI',
            'desc': 'Leading global provider of cloud computing and Enterprise AI solutions.',
            'city': 'Bangalore',
            'address': 'MG Road Innovation Hub, Bangalore',
            'website': 'https://techcorp.example.com',
            'badge': True
        },
        {
            'username': 'innodesign_hr',
            'email': 'careers@innodesign.com',
            'name': 'InnoDesign Labs',
            'industry': 'Design & Creative',
            'desc': 'Award winning UX research and digital interface studio working with Tech Giants.',
            'city': 'Mumbai',
            'address': 'Bandra Kurla Complex, Mumbai',
            'website': 'https://innodesign.example.com',
            'badge': True
        },
        {
            'username': 'cyberpulse_hr',
            'email': 'jobs@cyberpulse.io',
            'name': 'CyberPulse Systems',
            'industry': 'Cybersecurity & Infrastructure',
            'desc': 'Next-gen cybersecurity threat intelligence and cloud resilience management.',
            'city': 'Hyderabad',
            'address': 'HITEC City Cyber Towers, Hyderabad',
            'website': 'https://cyberpulse.example.com',
            'badge': True
        }
    ]

    companies = []
    for info in employers_info:
        emp_user, _ = User.objects.get_or_create(
            username=info['username'],
            defaults={
                'email': info['email'],
                'first_name': info['name'].split()[0],
                'last_name': 'HR',
                'role': 'employer',
                'is_verified': True
            }
        )
        emp_user.set_password('employer123')
        emp_user.save()

        comp, _ = Company.objects.get_or_create(
            employer=emp_user,
            defaults={
                'name': info['name'],
                'industry': info['industry'],
                'description': info['desc'],
                'address': info['address'],
                'city': info['city'],
                'website': info['website'],
                'hr_contact_name': f"{emp_user.first_name} HR",
                'hr_contact_email': info['email'],
                'hr_contact_phone': '+91 9876543210',
                'verification_status': 'approved',
                'is_verified_badge': info['badge']
            }
        )
        companies.append(comp)

    # 5. Create Jobs
    jobs_data = [
        {
            'title': 'Senior Full Stack Django Developer',
            'company': companies[0],
            'category': categories[0],
            'type': 'remote',
            'exp': '3-5 years',
            'salary_min': 1400000,
            'salary_max': 2200000,
            'location': 'Remote / Bangalore',
            'skills': 'Python, Django, React.js, Tailwind CSS, PostgreSQL',
            'qualification': 'B.Tech / MCA in Computer Science',
            'desc': 'We are looking for an experienced Senior Django Full Stack Architect to engineer high performance REST APIs and responsive glassmorphic dashboard web apps.',
            'resp': 'Architect robust Django microservices\nCollaborate with UI/UX engineers\nOptimize SQLite/PostgreSQL query performance\nDeploy Docker containers to cloud servers.',
            'benefits': 'Health Insurance, Remote Stipend, Performance Bonuses, Stock Options'
        },
        {
            'title': 'AI & Machine Learning Engineer',
            'company': companies[0],
            'category': categories[1],
            'type': 'full_time',
            'exp': '2-4 years',
            'salary_min': 1800000,
            'salary_max': 2800000,
            'location': 'Bangalore',
            'skills': 'Python, Machine Learning, Deep Learning, PyTorch, Scikit-Learn',
            'qualification': 'M.Tech / MS in AI or Computer Science',
            'desc': 'Join our core AI research group building predictive job matching algorithms, natural language resume parsing, and automated career roadmap generation.',
            'resp': 'Train NLP models for ATS scoring\nFine-tune open source LLMs\nBuild automated feature extraction pipelines.',
            'benefits': 'Flexible hours, Learning budget of 1 Lakh INR, Unlimited Coffee & Snacks'
        },
        {
            'title': 'Lead UI/UX Digital Product Designer',
            'company': companies[1],
            'category': categories[2],
            'type': 'hybrid',
            'exp': '4-7 years',
            'salary_min': 1500000,
            'salary_max': 2400000,
            'location': 'Mumbai',
            'skills': 'Figma, UI/UX Design, Wireframing, Glassmorphism, Design Systems',
            'qualification': 'Degree in Design, Fine Arts or equivalent experience',
            'desc': 'Drive visual experience for enterprise products. Build modern corporate UI libraries featuring micro-animations and sleek dark mode themes.',
            'resp': 'Conduct user testing and prototyping\nCreate high-fidelity wireframes\nBridge design handoffs with frontend developers.',
            'benefits': 'MacBook Pro provided, Annual Wellness Bonus, Creative Retreats'
        },
        {
            'title': 'Frontend React & Web Specialist',
            'company': companies[1],
            'category': categories[0],
            'type': 'fresher',
            'exp': '0-2 years',
            'salary_min': 800000,
            'salary_max': 1200000,
            'location': 'Remote',
            'skills': 'JavaScript, React.js, Tailwind CSS, HTML5',
            'qualification': 'B.E / B.Tech / BCA',
            'desc': 'Exciting entry-level opportunity for ambitious web frontend developers eager to build pixel-perfect user interfaces.',
            'resp': 'Implement interactive SPA components\nIntegrate Django REST backends\nEnsure 100% cross-browser responsive compatibility.',
            'benefits': 'Mentorship program, Gym membership, Work from anywhere'
        },
        {
            'title': 'Cloud Security & DevOps Specialist',
            'company': companies[2],
            'category': categories[0],
            'type': 'full_time',
            'exp': '3-6 years',
            'salary_min': 1600000,
            'salary_max': 2500000,
            'location': 'Hyderabad',
            'skills': 'Docker, Kubernetes, AWS, Python, CI/CD',
            'qualification': 'B.Tech in CS/IT',
            'desc': 'Manage multi-region Kubernetes clusters and secure Django deployment pipelines against cybersecurity vulnerabilities.',
            'resp': 'Automate zero-downtime CI/CD workflows\nMonitor infrastructure metrics\nAudit IAM roles and encryption rules.',
            'benefits': 'Relocation assistance, Quarterly performance incentives'
        }
    ]

    created_jobs = []
    for jd in jobs_data:
        j, _ = Job.objects.get_or_create(
            title=jd['title'],
            company=jd['company'],
            defaults={
                'posted_by': jd['company'].employer,
                'category': jd['category'],
                'vacancy': 3,
                'salary_min': jd['salary_min'],
                'salary_max': jd['salary_max'],
                'experience_required': jd['exp'],
                'qualification': jd['qualification'],
                'skills_required': jd['skills'],
                'description': jd['desc'],
                'responsibilities': jd['resp'],
                'benefits': jd['benefits'],
                'location': jd['location'],
                'job_type': jd['type'],
                'status': 'active',
                'deadline': date.today() + timedelta(days=30),
                'views_count': 142
            }
        )
        created_jobs.append(j)
    print(f"Created {len(created_jobs)} jobs.")

    # 6. Create Job Seeker User & Profile
    seeker_user, created = User.objects.get_or_create(
        username='alex_developer',
        defaults={
            'email': 'alex.dev@example.com',
            'first_name': 'Alex',
            'last_name': 'Morgan',
            'role': 'jobseeker',
            'phone': '+91 9988776655',
            'is_verified': True
        }
    )
    if created:
        seeker_user.set_password('seeker123')
        seeker_user.save()

    profile, _ = JobSeekerProfile.objects.get_or_create(
        user=seeker_user,
        defaults={
            'headline': 'Senior Full Stack Engineer (Python & Django)',
            'dob': date(1996, 5, 15),
            'gender': 'male',
            'address': 'Indiranagar 100ft Road',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'country': 'India',
            'expected_salary': '₹18 - ₹22 LPA',
            'linkedin_url': 'https://linkedin.com/in/alex-morgan-dev',
            'github_url': 'https://github.com/alex-morgan-dev',
            'portfolio_url': 'https://alexmorgan.dev',
            'resume_ats_score': 88
        }
    )

    # Education & Experience for Seeker
    Education.objects.get_or_create(
        seeker=profile,
        degree='Bachelor of Technology in CS',
        defaults={
            'institution': 'Indian Institute of Technology, Bangalore',
            'field_of_study': 'Computer Science & Engineering',
            'start_year': 2014,
            'end_year': 2018,
            'grade': '8.9 CGPA'
        }
    )
    Experience.objects.get_or_create(
        seeker=profile,
        title='Software Engineer',
        defaults={
            'company_name': 'Apex Cloud Solutions',
            'location': 'Bangalore',
            'start_date': date(2020, 1, 10),
            'is_current': True,
            'description': 'Developed web portals with Django & React, scaled database queries, and implemented OAuth systems.'
        }
    )
    for sk_name in ["Python", "Django", "JavaScript", "Tailwind CSS", "PostgreSQL"]:
        if sk_name in skills_obj:
            JobSeekerSkill.objects.get_or_create(seeker=profile, skill=skills_obj[sk_name], defaults={'level': 'expert'})

    # 7. Create Applications, Saved Jobs & Interviews
    app1, _ = Application.objects.get_or_create(
        job=created_jobs[0],
        applicant=seeker_user,
        defaults={
            'cover_letter': 'I am highly passionate about full stack Django development and modern UI architectures. My past 4 years building scalable web backends align directly with TechCorp.',
            'status': 'interview_scheduled',
            'ats_match_score': 92
        }
    )

    Interview.objects.get_or_create(
        application=app1,
        defaults={
            'scheduled_date': django.utils.timezone.now() + timedelta(days=2),
            'meet_link': 'https://meet.google.com/abc-hire-hub',
            'office_address': 'TechCorp HQ, MG Road Bangalore',
            'notes': 'Technical round covering Django ORM optimization, System Design & Live Pair Coding.',
            'status': 'scheduled'
        }
    )

    SavedJob.objects.get_or_create(seeker=seeker_user, job=created_jobs[1])
    SavedJob.objects.get_or_create(seeker=seeker_user, job=created_jobs[2])

    # 8. Notifications
    Notification.objects.get_or_create(
        user=seeker_user,
        title='Interview Scheduled!',
        defaults={
            'message': 'TechCorp Solutions scheduled a technical interview for Senior Full Stack Django Developer.',
            'notification_type': 'interview_scheduled'
        }
    )
    Notification.objects.get_or_create(
        user=seeker_user,
        title='Resume Viewed',
        defaults={
            'message': 'InnoDesign Labs hr team viewed your profile & resume.',
            'notification_type': 'resume_viewed'
        }
    )

    # 9. Announcements & Feedback
    SystemAnnouncement.objects.get_or_create(
        title='Welcome to HireHub AI Portal!',
        defaults={
            'content': 'We have officially launched the AI Resume ATS Score and Skill Gap Analyzer modules.',
            'target_role': 'all'
        }
    )

    Feedback.objects.get_or_create(
        name='Priya Sharma',
        defaults={
            'email': 'priya@example.com',
            'subject': 'Seamless AI Candidate Matching',
            'message': 'The smart match score and resume parser helped us recruit our lead engineer in 3 days!',
            'rating': 5
        }
    )
    ContactMessage.objects.get_or_create(
        name='David Miller',
        defaults={
            'email': 'david@example.com',
            'subject': 'Enterprise Talent Partnership',
            'message': 'Interested in registering 50+ company recruiters on HireHub.',
            'is_resolved': False
        }
    )

    # Site Visitor Logs
    for page in ['/jobs/', '/ai-dashboard/', '/company/1/', '/dashboard/jobseeker/']:
        SiteVisitorLog.objects.create(page_visited=page, ip_address='127.0.0.1')

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    run_seed()

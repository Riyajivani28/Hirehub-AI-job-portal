from django.shortcuts import render

def static_why_choose(request):
    return render(request, 'reports/why_choose.html')

def static_how_it_works(request):
    return render(request, 'reports/how_it_works.html')

def static_testimonials(request):
    return render(request, 'reports/testimonials.html')

def static_career_tips(request):
    return render(request, 'reports/career_tips.html')

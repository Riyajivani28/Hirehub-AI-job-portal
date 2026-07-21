from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import FeedbackForm, ContactForm

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            if request.user.is_authenticated:
                fb.user = request.user
            fb.save()
            messages.success(request, "Thank you for your valuable feedback!")
            return redirect('home')
    else:
        form = FeedbackForm()

    return render(request, 'feedback/feedback.html', {'form': form})

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been received. Our team will contact you within 24 hours!")
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'feedback/contact.html', {'form': form})

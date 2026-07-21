from django import forms
from .models import Application, Interview, OfferLetter

class ApplicationApplyForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']
        widgets = {
            'resume': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'cover_letter': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'rows': 4, 'placeholder': 'Write a compelling intro why you are the best fit...'}),
        }

class InterviewScheduleForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['scheduled_date', 'meet_link', 'office_address', 'notes']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'type': 'datetime-local'}),
            'meet_link': forms.URLInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'https://meet.google.com/xyz-abc-def'}),
            'office_address': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'Office physical address if in-person'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'rows': 3, 'placeholder': 'Preparation guidelines or interview topics'}),
        }

class OfferLetterForm(forms.ModelForm):
    class Meta:
        model = OfferLetter
        fields = ['joining_date', 'offered_salary', 'content']
        widgets = {
            'joining_date': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'type': 'date'}),
            'offered_salary': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'Annual CTC e.g. 1800000'}),
            'content': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'rows': 5, 'placeholder': 'Terms of employment, probation period, role expectations...'}),
        }

from django import forms
from .models import Job, Category

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'department', 'category', 'vacancy', 'job_type',
            'salary_min', 'salary_max', 'salary_negotiable', 'experience_required',
            'qualification', 'skills_required', 'location', 'deadline',
            'description', 'responsibilities', 'benefits'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'e.g. Senior Python Developer'}),
            'department': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'e.g. Engineering'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white'}),
            'vacancy': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'min': 1}),
            'job_type': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white'}),
            'salary_min': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white'}),
            'salary_max': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white'}),
            'salary_negotiable': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500 border-gray-300'}),
            'experience_required': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'e.g. 2-4 years'}),
            'qualification': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'e.g. B.Tech / MCA'}),
            'skills_required': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'Comma separated: Python, Django, React'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'placeholder': 'e.g. Bangalore / Remote'}),
            'deadline': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'rows': 4, 'placeholder': 'Job description and overall responsibilities'}),
            'responsibilities': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'rows': 3, 'placeholder': 'Bullet points of daily key responsibilities'}),
            'benefits': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 dark:text-white', 'rows': 2, 'placeholder': 'Perks, medical insurance, stock options...'}),
        }

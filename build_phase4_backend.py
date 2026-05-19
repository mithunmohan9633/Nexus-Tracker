import os

# 1. Update Models
models_py = '''from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('PM', 'Project Manager'),
        ('APM', 'Assistant Project Manager'),
        ('FA', 'Functional Analyst'),
        ('DEV', 'Developer'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='DEV')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    apm = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects', limit_choices_to={'profile__role': 'APM'})
    functional_analysts = models.ManyToManyField(User, related_name='assigned_fa_projects', blank=True, limit_choices_to={'profile__role': 'FA'})
    developers = models.ManyToManyField(User, related_name='assigned_dev_projects', blank=True, limit_choices_to={'profile__role': 'DEV'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review'),
        ('DONE', 'Done'),
    )
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    estimated_time_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_tickets')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'profile__role': 'DEV'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.pk} {self.title}"

class TicketRemark(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='remarks')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Remark by {self.author.username} on {self.ticket}"
'''
with open('issues/models.py', 'w', encoding='utf-8') as f:
    f.write(models_py)


# 2. Update Forms
forms_py = '''from django import forms
from .models import Project, Ticket, TicketRemark, UserProfile
from django.contrib.auth.models import User

class PMProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'apm']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'apm': forms.Select(attrs={'class': 'form-input'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['apm'].queryset = User.objects.filter(profile__role='APM')

class APMTeamForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['functional_analysts', 'developers']
        widgets = {
            'functional_analysts': forms.SelectMultiple(attrs={'class': 'form-input', 'style': 'height: 120px;'}),
            'developers': forms.SelectMultiple(attrs={'class': 'form-input', 'style': 'height: 120px;'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['functional_analysts'].queryset = User.objects.filter(profile__role='FA')
        self.fields['developers'].queryset = User.objects.filter(profile__role='DEV')

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['project', 'title', 'description', 'priority', 'assignee', 'estimated_time_hours']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'assignee': forms.Select(attrs={'class': 'form-input'}),
            'estimated_time_hours': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # FA can only create tickets in projects they are functional analysts on
            self.fields['project'].queryset = Project.objects.filter(functional_analysts=user)
            self.fields['assignee'].queryset = User.objects.filter(profile__role='DEV')

class RemarkForm(forms.ModelForm):
    class Meta:
        model = TicketRemark
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Add a remark...'}),
        }

class StatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': 'form-input'})}

class EmployeeCreationForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    class Meta:
        model = User
        fields = ['username', 'password', 'role']
        widgets = {'username': forms.TextInput(attrs={'class': 'form-input'})}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user
'''
with open('issues/forms.py', 'w', encoding='utf-8') as f:
    f.write(forms_py)

print("Models and forms built successfully.")

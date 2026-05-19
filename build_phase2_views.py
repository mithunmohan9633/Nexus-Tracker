import os

forms_py = '''from django import forms
from .models import Project, Ticket, TicketRemark, UserProfile
from django.contrib.auth.models import User

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'team']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'team': forms.SelectMultiple(attrs={'class': 'form-input'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show Devs and FAs in the team selection
        self.fields['team'].queryset = User.objects.filter(profile__role__in=['DEV', 'FA'])

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
            # FA can only create tickets in projects they are part of
            self.fields['project'].queryset = Project.objects.filter(team=user)
            # Only assign to Developers
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
'''
with open('issues/forms.py', 'w', encoding='utf-8') as f:
    f.write(forms_py)

views_py = '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Project, Ticket, TicketRemark, UserProfile
from .forms import ProjectForm, TicketForm, RemarkForm, StatusForm

def get_role(user):
    try:
        return user.profile.role
    except:
        return None

@login_required
def dashboard(request):
    role = get_role(request.user)
    
    if role == 'PM':
        projects = Project.objects.all()
        tickets = Ticket.objects.all()
        context = {
            'role_title': 'Project Manager',
            'projects_count': projects.count(),
            'open_tickets': tickets.exclude(status='DONE').count(),
            'closed_tickets': tickets.filter(status='DONE').count(),
            'recent_projects': projects.order_by('-created_at')[:5]
        }
        return render(request, 'dashboard_pm.html', context)
        
    elif role == 'APM':
        projects = Project.objects.filter(apm=request.user)
        context = {
            'role_title': 'Assistant Project Manager',
            'my_projects': projects,
        }
        return render(request, 'dashboard_apm.html', context)
        
    elif role == 'FA':
        projects = Project.objects.filter(team=request.user)
        tickets = Ticket.objects.filter(reporter=request.user).order_by('-updated_at')
        context = {
            'role_title': 'Functional Analyst',
            'my_projects_count': projects.count(),
            'my_reported_tickets': tickets[:10],
        }
        return render(request, 'dashboard_fa.html', context)
        
    else: # DEV
        tickets = Ticket.objects.filter(assignee=request.user).order_by('-updated_at')
        context = {
            'role_title': 'Developer',
            'open_tasks': tickets.exclude(status='DONE'),
            'completed_tasks': tickets.filter(status='DONE'),
        }
        return render(request, 'dashboard_dev.html', context)

@login_required
def project_create(request):
    if get_role(request.user) not in ['PM', 'APM']:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            if get_role(request.user) == 'APM':
                p.apm = request.user
            p.save()
            form.save_m2m() # save team
            return redirect('dashboard')
    else:
        form = ProjectForm()
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Create Project'})

@login_required
def ticket_create(request):
    if get_role(request.user) != 'FA':
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reporter = request.user
            ticket.save()
            return redirect('dashboard')
    else:
        form = TicketForm(user=request.user)
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Create Issue'})

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    role = get_role(request.user)
    
    # Check permissions
    if role == 'DEV' and ticket.assignee != request.user:
        return redirect('dashboard')
        
    remark_form = RemarkForm()
    status_form = StatusForm(instance=ticket)
    
    if request.method == 'POST':
        if 'add_remark' in request.POST:
            rform = RemarkForm(request.POST)
            if rform.is_valid():
                r = rform.save(commit=False)
                r.ticket = ticket
                r.author = request.user
                r.save()
                return redirect('ticket_detail', pk=pk)
        elif 'update_status' in request.POST and role == 'DEV':
            sform = StatusForm(request.POST, instance=ticket)
            if sform.is_valid():
                sform.save()
                return redirect('ticket_detail', pk=pk)

    return render(request, 'issues/ticket_detail.html', {
        'ticket': ticket,
        'remark_form': remark_form,
        'status_form': status_form,
        'role': role
    })
'''
with open('issues/views.py', 'w', encoding='utf-8') as f:
    f.write(views_py)

urls_py = '''from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('projects/new/', views.project_create, name='project_create'),
    path('tickets/new/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
]
'''
with open('issues/urls.py', 'w', encoding='utf-8') as f:
    f.write(urls_py)

print("Phase 2 Views and Forms compiled.")

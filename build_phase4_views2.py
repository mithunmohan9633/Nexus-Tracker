import os

views_py = '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Project, Ticket, TicketRemark, UserProfile
from .forms import PMProjectForm, APMTeamForm, TicketForm, RemarkForm, StatusForm, EmployeeCreationForm
from django.contrib.auth.models import User

def get_role(user):
    try:
        return user.profile.role
    except:
        return None

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('hr_dashboard')
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
        projects = Project.objects.filter(functional_analysts=request.user)
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
def hr_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    employees = UserProfile.objects.all().select_related('user')
    context = {
        'role_title': 'HR / Administration',
        'total_employees': employees.count(),
        'projects_count': Project.objects.count(),
        'employees': employees
    }
    return render(request, 'dashboard_hr.html', context)

@login_required
def employee_create(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hr_dashboard')
    else:
        form = EmployeeCreationForm()
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Create New Employee'})

@login_required
def employee_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, pk=pk)
        if not user_to_delete.is_superuser:
            user_to_delete.delete()
    return redirect('hr_dashboard')

@login_required
def project_create(request):
    if get_role(request.user) != 'PM':
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = PMProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = PMProjectForm()
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Initialize Project'})

@login_required
def project_edit_team(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if get_role(request.user) != 'APM' or project.apm != request.user:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = APMTeamForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = APMTeamForm(instance=project)
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Manage Project Team'})

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
    path('hr/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/employees/new/', views.employee_create, name='employee_create'),
    path('hr/employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('projects/new/', views.project_create, name='project_create'),
    path('projects/<int:pk>/team/', views.project_edit_team, name='project_edit_team'),
    path('tickets/new/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
]
'''
with open('issues/urls.py', 'w', encoding='utf-8') as f:
    f.write(urls_py)

admin_py = '''from django.contrib import admin
from .models import UserProfile, Project, Ticket, TicketRemark

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'apm', 'created_at')
    filter_horizontal = ('functional_analysts', 'developers')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'assignee', 'reporter')
    list_filter = ('status', 'priority', 'project')

admin.site.register(TicketRemark)
'''
with open('issues/admin.py', 'w', encoding='utf-8') as f:
    f.write(admin_py)

print("Views, URLs, and Admin updated successfully.")

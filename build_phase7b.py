import os

# 2. Rewrite views.py with full QA verification flow
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
        project_workloads = []
        grand_total_pending = 0
        for p in projects:
            pending_tickets = p.tickets.exclude(status='DONE')
            dev_workloads = []
            for dev in p.developers.all():
                dev_workloads.append({
                    'developer': dev,
                    'pending_count': pending_tickets.filter(assignee=dev).count()
                })
            project_workloads.append({
                'project': p,
                'total_pending': pending_tickets.count(),
                'unassigned_count': pending_tickets.filter(assignee__isnull=True).count(),
                'dev_workloads': dev_workloads
            })
            grand_total_pending += pending_tickets.count()
        
        # Tickets awaiting FA verification across all projects
        verification_tickets = Ticket.objects.filter(
            project__in=projects, status='PENDING_REVIEW'
        ).order_by('-updated_at')
        
        context = {
            'role_title': 'Functional Analyst',
            'my_projects_count': projects.count(),
            'project_workloads': project_workloads,
            'grand_total_pending': grand_total_pending,
            'verification_tickets': verification_tickets,
            'verification_count': verification_tickets.count(),
        }
        return render(request, 'dashboard_fa.html', context)

    else:  # DEV
        tickets = Ticket.objects.filter(assignee=request.user).order_by('-updated_at')
        context = {
            'role_title': 'Developer',
            'open_tasks': tickets.exclude(status__in=['DONE', 'PENDING_REVIEW']),
            'pending_review_tasks': tickets.filter(status='PENDING_REVIEW'),
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
    return render(request, 'issues/generic_form.html', {'form': form, 'title': f'Manage Team — {project.name}'})


@login_required
def ticket_create(request):
    if get_role(request.user) != 'FA':
        return redirect('dashboard')
    project_id = request.GET.get('project')
    if not project_id:
        return redirect('dashboard')
    project = get_object_or_404(Project, pk=project_id)
    if request.user not in project.functional_analysts.all():
        return redirect('dashboard')
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reporter = request.user
            ticket.project = project
            ticket.save()
            return redirect('dashboard')
    else:
        form = TicketForm()
    return render(request, 'issues/ticket_form.html', {'form': form, 'title': f'Log Issue — {project.name}', 'project': project})


@login_required
def ticket_verify(request, pk):
    """FA approves or rejects a PENDING_REVIEW ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)
    if get_role(request.user) != 'FA':
        return redirect('dashboard')
    if ticket.status != 'PENDING_REVIEW':
        return redirect('ticket_detail', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            ticket.status = 'DONE'
            ticket.save()
            TicketRemark.objects.create(
                ticket=ticket,
                author=request.user,
                text='✅ Bug verified and approved by Functional Analyst. Ticket closed.',
                is_system=True
            )
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'No reason provided.')
            ticket.status = 'IN_PROGRESS'
            ticket.save()
            TicketRemark.objects.create(
                ticket=ticket,
                author=request.user,
                text=f'❌ Bug verification FAILED. Returned to Developer for fix.\nReason: {reason}',
                is_system=True
            )
    return redirect('dashboard')


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


@login_required
def ticket_filtered_list(request):
    if get_role(request.user) != 'FA':
        return redirect('dashboard')
    project_id = request.GET.get('project')
    developer_id = request.GET.get('dev')
    allowed_projects = Project.objects.filter(functional_analysts=request.user)
    tickets = Ticket.objects.filter(project__in=allowed_projects).exclude(status='DONE').order_by('-updated_at')
    title = "All Pending Issues Across All Projects"
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        if project not in allowed_projects:
            return redirect('dashboard')
        tickets = tickets.filter(project=project)
        title = f"Pending Issues in {project.name}"
    if developer_id:
        if developer_id == 'none':
            tickets = tickets.filter(assignee__isnull=True)
            title += " (Unassigned)"
        else:
            dev = get_object_or_404(User, pk=developer_id)
            tickets = tickets.filter(assignee=dev)
            title += f" assigned to {dev.username}"
    return render(request, 'issues/ticket_filtered_list.html', {'tickets': tickets, 'title': title})
'''
with open('issues/views.py', 'w', encoding='utf-8') as f:
    f.write(views_py)


# Update StatusForm to restrict DEV to only IN_PROGRESS and PENDING_REVIEW
with open('issues/forms.py', 'r', encoding='utf-8') as f:
    forms_py = f.read()

old_status = '''class StatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': 'form-input'})}'''

new_status = '''class DevStatusForm(forms.ModelForm):
    """Restricted Status form for Developers - cannot set DONE directly."""
    status = forms.ChoiceField(
        choices=[('IN_PROGRESS', 'In Progress'), ('PENDING_REVIEW', 'Submit for FA Review')],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    class Meta:
        model = Ticket
        fields = ['status']

class StatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': 'form-input'})}'''

forms_py = forms_py.replace(old_status, new_status)
with open('issues/forms.py', 'w', encoding='utf-8') as f:
    f.write(forms_py)


# Update urls.py
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
    path('tickets/<int:pk>/verify/', views.ticket_verify, name='ticket_verify'),
    path('tickets/filter/', views.ticket_filtered_list, name='ticket_filtered_list'),
]
'''
with open('issues/urls.py', 'w', encoding='utf-8') as f:
    f.write(urls_py)

print("Views and URLs updated.")

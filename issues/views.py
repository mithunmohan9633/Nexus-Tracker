from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Project, Ticket, TicketRemark, UserProfile, Message
from .forms import PMProjectForm, APMTeamForm, TicketForm, RemarkForm, StatusForm, EmployeeCreationForm, ComposeMessageForm
from django.contrib.auth.models import User


def get_role(user):
    try:
        return user.profile.role
    except Exception:
        return None


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('hr_dashboard')
    role = get_role(request.user)

    if role == 'PM':
        projects = Project.objects.filter(is_deleted=False, is_completed=False)
        tickets = Ticket.objects.all()
        context = {
            'role_title': 'Project Manager',
            'projects_count': projects.count(),
            'open_tickets': tickets.exclude(status='DONE').count(),
            'closed_tickets': tickets.filter(status='DONE').count(),
            'recent_projects': projects.order_by('-created_at')[:5],
        }
        return render(request, 'dashboard_pm.html', context)

    elif role == 'APM':
        projects = Project.objects.filter(apm=request.user, is_deleted=False, is_completed=False)
        tickets = Ticket.objects.filter(project__in=projects)
        context = {
            'role_title': 'Assistant Project Manager',
            'my_projects': projects,
            'projects_count': projects.count(),
            'open_tickets': tickets.exclude(status='DONE').count(),
            'closed_tickets': tickets.filter(status='DONE').count(),
            'recent_projects': projects.order_by('-created_at')[:5],
        }
        return render(request, 'dashboard_apm.html', context)

    elif role == 'FA':
        projects = Project.objects.filter(functional_analysts=request.user, is_deleted=False, is_completed=False)
        project_workloads = []
        grand_total_pending = 0
        for p in projects:
            pending_tickets = p.tickets.exclude(status='DONE')
            dev_workloads = []
            for dev in p.developers.all():
                dev_workloads.append({
                    'developer': dev,
                    'pending_count': pending_tickets.filter(assignee=dev).count(),
                })
            project_workloads.append({
                'project': p,
                'total_pending': pending_tickets.count(),
                'unassigned_count': pending_tickets.filter(assignee__isnull=True).count(),
                'dev_workloads': dev_workloads,
            })
            grand_total_pending += pending_tickets.count()

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

    else:
        tickets = Ticket.objects.filter(assignee=request.user).order_by('-updated_at')
        active_bugs = tickets.exclude(status='DONE')
        context = {
            'role_title': 'Developer',
            'open_tasks': active_bugs.exclude(status='PENDING_REVIEW'),
            'pending_review_tasks': active_bugs.filter(status='PENDING_REVIEW'),
            'all_active_bugs': active_bugs,
        }
        return render(request, 'dashboard_dev.html', context)


@login_required
def hr_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    employees = UserProfile.objects.all().select_related('user')
    projects_detailed = Project.objects.all()
    context = {
        'role_title': 'HR / Administration',
        'total_employees': employees.count(),
        'projects_count': Project.objects.count(),
        'employees': employees,
        'projects_detailed': projects_detailed,
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
            old_fas = set(project.functional_analysts.all())
            old_devs = set(project.developers.all())
            
            form.save()
            
            new_fas = set(project.functional_analysts.all())
            new_devs = set(project.developers.all())
            
            added_fas = new_fas - old_fas
            added_devs = new_devs - old_devs
            newly_assigned = added_fas.union(added_devs)
            
            for user in newly_assigned:
                msg = Message.objects.create(
                    project=project,
                    subject=f"Assigned to New Project: {project.name}",
                    body=f"""You have been assigned to the project '{project.name}'.

Deadline: {project.deadline or 'Not set'}

Description: {project.description}"""
                )
                msg.recipients.add(user)
            
            return redirect('dashboard')
    else:
        form = APMTeamForm(instance=project)
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Manage Team'})


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
        form = TicketForm(request.POST, project=project)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reporter = request.user
            ticket.project = project
            ticket.save()
            return redirect('dashboard')
    else:
        form = TicketForm(project=project)
    return render(request, 'issues/ticket_form.html', {
        'form': form,
        'title': 'Log Issue for ' + project.name,
        'project': project,
    })


@login_required
def ticket_verify(request, pk):
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
                text='Bug verified and approved by Functional Analyst. Ticket closed.',
                is_system=True,
            )
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'No reason provided.')
            ticket.status = 'IN_PROGRESS'
            ticket.save()
            TicketRemark.objects.create(
                ticket=ticket,
                author=request.user,
                text='Bug verification FAILED. Returned to Developer. Reason: ' + reason,
                is_system=True,
            )
    return redirect('dashboard')


@login_required
def ticket_reassign(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if get_role(request.user) != 'DEV' or ticket.assignee != request.user:
        return redirect('dashboard')
    if request.method == 'POST':
        new_dev_id = request.POST.get('new_assignee')
        if new_dev_id:
            new_dev = get_object_or_404(User, pk=new_dev_id)
            if new_dev in ticket.project.developers.all() and new_dev != request.user:
                old_name = request.user.username
                ticket.assignee = new_dev
                ticket.status = 'IN_PROGRESS'
                ticket.save()
                TicketRemark.objects.create(
                    ticket=ticket,
                    author=request.user,
                    text='Bug reassigned from ' + old_name + ' to ' + new_dev.username + ' within the project team.',
                    is_system=True,
                )
    return redirect('dashboard')


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    role = get_role(request.user)
    if role == 'DEV' and ticket.assignee != request.user:
        return redirect('dashboard')

    # FA can view any ticket in their assigned projects
    if role == 'FA':
        fa_projects = Project.objects.filter(functional_analysts=request.user, is_deleted=False, is_completed=False)
        if ticket.project not in fa_projects:
            return redirect('dashboard')
    other_devs = ticket.project.developers.exclude(pk=request.user.pk) if role == 'DEV' else None

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
            new_status = request.POST.get('status')
            if new_status in ['IN_PROGRESS', 'PENDING_REVIEW']:
                ticket.status = new_status
                ticket.save()
                if new_status == 'PENDING_REVIEW':
                    TicketRemark.objects.create(
                        ticket=ticket,
                        author=request.user,
                        text='Developer ' + request.user.username + ' submitted this bug for Functional Analyst review.',
                        is_system=True,
                    )
            return redirect('ticket_detail', pk=pk)

        elif 'fa_reassign' in request.POST and role == 'FA':
            new_dev_id = request.POST.get('new_assignee_fa')
            if new_dev_id:
                new_dev = get_object_or_404(User, pk=new_dev_id)
                if new_dev in ticket.project.developers.all():
                    old_name = ticket.assignee.username if ticket.assignee else 'Unassigned'
                    ticket.assignee = new_dev
                    ticket.status = 'IN_PROGRESS'
                    ticket.save()
                    TicketRemark.objects.create(
                        ticket=ticket,
                        author=request.user,
                        text='FA redirected this bug from ' + old_name + ' to ' + new_dev.username + ' for resolution.',
                        is_system=True,
                    )
            return redirect('ticket_detail', pk=pk)

    return render(request, 'issues/ticket_detail.html', {
        'ticket': ticket,
        'remark_form': remark_form,
        'status_form': status_form,
        'role': role,
        'other_devs': other_devs,
    })


@login_required
def ticket_filtered_list(request):
    if get_role(request.user) != 'FA':
        return redirect('dashboard')
    project_id = request.GET.get('project')
    developer_id = request.GET.get('dev')
    allowed_projects = Project.objects.filter(functional_analysts=request.user, is_deleted=False, is_completed=False)
    tickets = Ticket.objects.filter(project__in=allowed_projects).exclude(status='DONE').order_by('-updated_at')
    title = 'All Pending Issues Across All Projects'
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        if project not in allowed_projects:
            return redirect('dashboard')
        tickets = tickets.filter(project=project)
        title = 'Pending Issues in ' + project.name
    if developer_id:
        if developer_id == 'none':
            tickets = tickets.filter(assignee__isnull=True)
            title += ' (Unassigned)'
        else:
            dev = get_object_or_404(User, pk=developer_id)
            tickets = tickets.filter(assignee=dev)
            title += ' assigned to ' + dev.username
    return render(request, 'issues/ticket_filtered_list.html', {'tickets': tickets, 'title': title})




@login_required
def inbox_view(request):
    messages = Message.objects.filter(recipients=request.user).order_by('-created_at')
    return render(request, 'issues/inbox.html', {'messages': messages})

@login_required
def message_detail_view(request, pk):
    msg = get_object_or_404(Message, pk=pk, recipients=request.user)
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    return render(request, 'issues/message_detail.html', {'msg': msg})

@login_required
def compose_message_view(request):
    if request.method == 'POST':
        form = ComposeMessageForm(request.POST, exclude_user=request.user)
        if form.is_valid():
            recipients = form.cleaned_data['recipients']
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            project = form.cleaned_data.get('project')
            for recipient in recipients:
                msg = Message.objects.create(
                    sender=request.user,
                    subject=subject,
                    body=body,
                )
                msg.recipients.add(recipient)
            return redirect('inbox')
    else:
        recipient_id = request.GET.get('to')
        initial = {}
        if recipient_id:
            initial['recipients'] = [recipient_id]
        form = ComposeMessageForm(initial=initial, exclude_user=request.user)
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Compose Message'})


@login_required
def check_notifications(request):
    count = Message.objects.filter(recipients=request.user, is_read=False).count()
    latest = Message.objects.filter(recipients=request.user, is_read=False).order_by('-created_at').first()
    data = {'unread_count': count}
    if latest:
        data['latest_subject'] = latest.subject
        data['latest_sender'] = latest.sender.username if latest.sender else 'System'
        data['latest_id'] = latest.pk
    return JsonResponse(data)

@login_required
def message_json_view(request, pk):
    msg = get_object_or_404(Message, pk=pk, recipients=request.user)
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    
    return JsonResponse({
        'id': msg.pk,
        'subject': msg.subject,
        'sender': msg.sender.username if msg.sender else 'System',
        'date': msg.created_at.strftime("%b %d, %Y %H:%M"),
        'body': msg.body,
        'project': msg.project.name if msg.project else None,
        'sender_id': msg.sender.pk if msg.sender else None
    })

@login_required
def employee_detail_view(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    target_user = get_object_or_404(User, pk=pk)
    profile = target_user.profile
    
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name')
        profile.mobile_number = request.POST.get('mobile_number')
        target_user.email = request.POST.get('email')
        profile.role = request.POST.get('role')
        target_user.save()
        profile.save()
        return redirect('hr_dashboard')
        
    return render(request, 'issues/employee_detail.html', {'target_user': target_user, 'profile': profile})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Access control: Only PM, HR, or assigned members can view
    is_pm = hasattr(request.user, 'profile') and request.user.profile.role == 'PM'
    is_hr = hasattr(request.user, 'profile') and request.user.profile.role == 'HR'
    is_apm = project.apm == request.user
    is_fa = project.functional_analysts.filter(pk=request.user.pk).exists()
    is_dev = project.developers.filter(pk=request.user.pk).exists()
    
    if not (is_pm or is_hr or is_apm or is_fa or is_dev):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You do not have access to view this project.")
        
    tickets = project.tickets.all()
    total_tickets = tickets.count()
    done_tickets = tickets.filter(status='DONE').count()
    progress = int((done_tickets / total_tickets * 100) if total_tickets > 0 else 0)
    
    context = {
        'project': project,
        'tickets': tickets,
        'total_tickets': total_tickets,
        'done_tickets': done_tickets,
        'progress': progress,
        'is_pm_or_apm': is_pm or is_apm
    }
    return render(request, 'issues/project_detail.html', context)

@login_required
def project_complete(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        
        # Only PM or APM of this project can complete it
        is_pm = hasattr(request.user, 'profile') and request.user.profile.role == 'PM'
        is_apm = project.apm == request.user
        
        if not (is_pm or is_apm):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Only PMs and assigned APMs can mark projects as completed.")
            
        project.is_completed = True
        project.save()
        return redirect('dashboard')
    return redirect('dashboard')

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

def get_timeframe_filter(request, date_field):
    timeframe = request.GET.get('filter', 'all')
    now = timezone.now()
    if timeframe == '7days':
        return Q(**{f"{date_field}__gte": now - timedelta(days=7)})
    elif timeframe == '30days':
        return Q(**{f"{date_field}__gte": now - timedelta(days=30)})
    elif timeframe == 'month':
        return Q(**{f"{date_field}__month": now.month, f"{date_field}__year": now.year})
    return Q()

@login_required
def project_list_all(request):
    projects = Project.objects.filter(is_deleted=False, is_completed=False).order_by('-created_at')
    return render(request, 'issues/project_list_all.html', {'projects': projects})

@login_required
def bugs_open_list(request):
    time_filter = get_timeframe_filter(request, 'created_at')
    projects = Project.objects.filter(is_completed=False).annotate(
        bug_count=Count('tickets', filter=time_filter & Q(tickets__status__in=['TODO', 'IN_PROGRESS', 'PENDING_REVIEW']))
    ).filter(bug_count__gt=0).order_by('-bug_count')
    return render(request, 'issues/bugs_summary_list.html', {
        'projects': projects, 
        'title': 'System Open Bugs', 
        'type': 'open',
        'current_filter': request.GET.get('filter', 'all')
    })

@login_required
def bugs_closed_list(request):
    time_filter = get_timeframe_filter(request, 'completed_at')
    projects = Project.objects.filter(is_completed=False).annotate(
        bug_count=Count('tickets', filter=time_filter & Q(tickets__status='DONE'))
    ).filter(bug_count__gt=0).order_by('-bug_count')
    return render(request, 'issues/bugs_summary_list.html', {
        'projects': projects, 
        'title': 'System Closed Bugs', 
        'type': 'closed',
        'current_filter': request.GET.get('filter', 'all')
    })

@login_required
def bugs_open_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    time_filter = get_timeframe_filter(request, 'created_at')
    tickets = project.tickets.filter(time_filter & Q(status__in=['TODO', 'IN_PROGRESS', 'PENDING_REVIEW']))
    
    # Group by dev
    dev_stats = User.objects.filter(assigned_tickets__in=tickets).annotate(count=Count('assigned_tickets')).distinct()
    
    # FA is at project level, but we can list the project's FAs
    fas = project.functional_analysts.all()
    
    return render(request, 'issues/bugs_drilldown.html', {
        'project': project,
        'title': f'Open Bugs: {project.name}',
        'type': 'open',
        'tickets': tickets,
        'dev_stats': dev_stats,
        'fas': fas,
        'current_filter': request.GET.get('filter', 'all')
    })

@login_required
def bugs_closed_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    time_filter = get_timeframe_filter(request, 'completed_at')
    tickets = project.tickets.filter(time_filter & Q(status='DONE'))
    
    dev_stats = User.objects.filter(assigned_tickets__in=tickets).annotate(count=Count('assigned_tickets')).distinct()
    fas = project.functional_analysts.all()
    
    return render(request, 'issues/bugs_drilldown.html', {
        'project': project,
        'title': f'Closed Bugs: {project.name}',
        'type': 'closed',
        'tickets': tickets,
        'dev_stats': dev_stats,
        'fas': fas,
        'current_filter': request.GET.get('filter', 'all')
    })

@login_required
def reassign_ticket_apm(request, ticket_pk):
    ticket = get_object_or_404(Ticket, pk=ticket_pk)
    project = ticket.project

    # Only the APM of this project can reassign
    if project.apm != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Only the APM of this project can reassign tickets.")

    if request.method == 'POST':
        new_assignee_id = request.POST.get('new_assignee')
        if new_assignee_id:
            new_assignee = get_object_or_404(User, pk=new_assignee_id)
            old_assignee = ticket.assignee
            ticket.assignee = new_assignee
            ticket.save()

            # Notify the new assignee
            msg = Message.objects.create(
                sender=request.user,
                subject=f"Ticket Reassigned: {ticket.title}",
                body=f"You have been assigned a ticket in project '{project.name}'.\n\nTicket: {ticket.title}\nPriority: {ticket.get_priority_display()}"
            )
            msg.recipients.add(new_assignee)
        return redirect('manage_team_apm', pk=project.pk)
    return redirect('manage_team_apm', pk=project.pk)

@login_required
def manage_team_apm(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.apm != request.user and not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied()

    if request.method == 'POST':
        form = APMTeamForm(request.POST, instance=project)
        if form.is_valid():
            old_fas = set(project.functional_analysts.all())
            old_devs = set(project.developers.all())
            form.save()
            new_fas = set(project.functional_analysts.all())
            new_devs = set(project.developers.all())
            newly_assigned = (new_fas - old_fas).union(new_devs - old_devs)
            for user in newly_assigned:
                msg = Message.objects.create(
                    project=project,
                    subject=f"Assigned to Project: {project.name}",
                    body=f"You have been assigned to the project '{project.name}'.\n\nDeadline: {project.deadline or 'Not set'}\n\nDescription: {project.description}"
                )
                msg.recipients.add(user)
            return redirect('manage_team_apm', pk=pk)
    else:
        form = APMTeamForm(instance=project)

    open_tickets = project.tickets.exclude(status='DONE')
    developers = project.developers.all()
    context = {
        'project': project,
        'form': form,
        'open_tickets': open_tickets,
        'developers': developers,
    }
    return render(request, 'issues/manage_team_apm.html', context)


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'PM'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Only PM can delete projects.")

    if request.method == 'POST':
        if not project.is_completed:
            reason = request.POST.get('reason')
            if reason:
                project.delete_reason = reason
        project.is_deleted = True
        project.save()
        return redirect('dashboard')
    return redirect('project_detail', pk=pk)

@login_required
def project_archived_list(request):
    projects = Project.objects.filter(Q(is_deleted=True) | Q(is_completed=True)).order_by('-created_at')
    return render(request, 'issues/project_archived_list.html', {'projects': projects})

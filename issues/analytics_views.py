import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Ticket, Project

@login_required
def analytics_dashboard(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'PM':
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Only Project Managers can view Analytics.")

    timeframe = request.GET.get('filter', 'all')
    now = timezone.now()
    
    if timeframe == '7days':
        date_filter = Q(created_at__gte=now - timedelta(days=7))
    elif timeframe == '30days':
        date_filter = Q(created_at__gte=now - timedelta(days=30))
    else:
        date_filter = Q()

    # DEV Metrics
    dev_users = User.objects.filter(profile__role='DEV')
    dev_names = []
    dev_completed = []
    dev_in_progress = []
    dev_todo = []
    for dev in dev_users:
        dev_names.append(dev.profile.full_name or dev.username)
        tickets = Ticket.objects.filter(assignee=dev).filter(date_filter)
        dev_completed.append(tickets.filter(status='DONE').count())
        dev_in_progress.append(tickets.filter(status='IN_PROGRESS').count())
        dev_todo.append(tickets.filter(status='TODO').count())
        
    dev_metrics = {
        'names': dev_names,
        'completed': dev_completed,
        'in_progress': dev_in_progress,
        'todo': dev_todo,
    }

    # APM Metrics
    apm_users = User.objects.filter(profile__role='APM')
    apm_names = []
    apm_project_counts = []
    for apm in apm_users:
        apm_names.append(apm.profile.full_name or apm.username)
        if timeframe == '7days':
            p_filter = Q(created_at__gte=now - timedelta(days=7))
        elif timeframe == '30days':
            p_filter = Q(created_at__gte=now - timedelta(days=30))
        else:
            p_filter = Q()
        apm_project_counts.append(Project.objects.filter(apm=apm).filter(p_filter).count())
        
    apm_metrics = {
        'names': apm_names,
        'project_counts': apm_project_counts
    }

    # FA Metrics
    fa_users = User.objects.filter(profile__role='FA')
    fa_names = []
    fa_pending_reviews = []
    for fa in fa_users:
        fa_names.append(fa.profile.full_name or fa.username)
        fa_pending_reviews.append(
            Ticket.objects.filter(project__functional_analysts=fa, status='PENDING_REVIEW').filter(date_filter).count()
        )
        
    fa_metrics = {
        'names': fa_names,
        'pending_reviews': fa_pending_reviews
    }

    # Tickets by Priority (New Graph)
    priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    priority_counts = []
    for p in priorities:
        priority_counts.append(Ticket.objects.filter(priority=p).filter(date_filter).count())
        
    priority_metrics = {
        'labels': ['Low', 'Medium', 'High', 'Critical'],
        'counts': priority_counts
    }

    # Tickets by Project (New Graph)
    projects = Project.objects.all()
    proj_names = []
    proj_ticket_counts = []
    for p in projects:
        proj_names.append(p.name)
        proj_ticket_counts.append(Ticket.objects.filter(project=p).filter(date_filter).count())
        
    project_metrics = {
        'names': proj_names,
        'counts': proj_ticket_counts
    }

    context = {
        'current_filter': timeframe,
        'dev_metrics_json': json.dumps(dev_metrics, cls=DjangoJSONEncoder),
        'apm_metrics_json': json.dumps(apm_metrics, cls=DjangoJSONEncoder),
        'fa_metrics_json': json.dumps(fa_metrics, cls=DjangoJSONEncoder),
        'priority_metrics_json': json.dumps(priority_metrics, cls=DjangoJSONEncoder),
        'project_metrics_json': json.dumps(project_metrics, cls=DjangoJSONEncoder),
    }
    return render(request, 'issues/analytics_dashboard.html', context)

import os

with open('issues/views.py', 'r', encoding='utf-8') as f:
    views_content = f.read()

# 1. Update FA dashboard context to calculate grand_total_pending
old_fa = '''    elif role == 'FA':
        projects = Project.objects.filter(functional_analysts=request.user)
        project_workloads = []
        for p in projects:'''

new_fa = '''    elif role == 'FA':
        projects = Project.objects.filter(functional_analysts=request.user)
        project_workloads = []
        grand_total_pending = 0
        for p in projects:'''

views_content = views_content.replace(old_fa, new_fa)

old_fa_context = '''            project_workloads.append({
                'project': p,
                'total_pending': pending_tickets.count(),
                'unassigned_count': pending_tickets.filter(assignee__isnull=True).count(),
                'dev_workloads': dev_workloads
            })
        context = {
            'role_title': 'Functional Analyst',
            'my_projects_count': projects.count(),
            'project_workloads': project_workloads,
        }'''

new_fa_context = '''            project_workloads.append({
                'project': p,
                'total_pending': pending_tickets.count(),
                'unassigned_count': pending_tickets.filter(assignee__isnull=True).count(),
                'dev_workloads': dev_workloads
            })
            grand_total_pending += pending_tickets.count()
        context = {
            'role_title': 'Functional Analyst',
            'my_projects_count': projects.count(),
            'project_workloads': project_workloads,
            'grand_total_pending': grand_total_pending,
        }'''

views_content = views_content.replace(old_fa_context, new_fa_context)

# 2. Update ticket_filtered_list security and title
old_filter_view = '''@login_required
def ticket_filtered_list(request):
    if get_role(request.user) != 'FA':
        return redirect('dashboard')
        
    project_id = request.GET.get('project')
    developer_id = request.GET.get('dev')
    
    tickets = Ticket.objects.exclude(status='DONE').order_by('-updated_at')
    title = "Pending Points"
    
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        tickets = tickets.filter(project=project)
        title += f" in {project.name}"'''

new_filter_view = '''@login_required
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
        title = f"Pending Issues in {project.name}"'''

views_content = views_content.replace(old_filter_view, new_filter_view)

with open('issues/views.py', 'w', encoding='utf-8') as f:
    f.write(views_content)


# 3. Update dashboard_fa.html
with open('templates/dashboard_fa.html', 'r', encoding='utf-8') as f:
    fa_html = f.read()

old_metrics = '''<div class="metrics-grid">
    <div class="metric-card">
        <h3>Assigned Projects</h3>
        <div class="value">{{ my_projects_count }}</div>
    </div>
</div>'''

new_metrics = '''<div class="metrics-grid">
    <div class="metric-card">
        <h3>Assigned Projects</h3>
        <div class="value">{{ my_projects_count }}</div>
    </div>
    <div class="metric-card" style="border-color: var(--accent-red); transition: all 0.2s; cursor: pointer;" onclick="window.location.href='{% url 'ticket_filtered_list' %}'">
        <h3 style="color: var(--accent-red);">Grand Total Pending Points</h3>
        <div class="value">{{ grand_total_pending }}</div>
        <div style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">Click to view all open items across all projects ↗</div>
    </div>
</div>'''

fa_html = fa_html.replace(old_metrics, new_metrics)
with open('templates/dashboard_fa.html', 'w', encoding='utf-8') as f:
    f.write(fa_html)

print("FA Grand Total Metric built successfully.")

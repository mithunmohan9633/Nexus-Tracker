import os

with open('issues/views.py', 'r', encoding='utf-8') as f:
    views_content = f.read()

# We will just append the new filter view and replace the FA block.
# Finding the FA block
old_fa = '''    elif role == 'FA':
        projects = Project.objects.filter(functional_analysts=request.user)
        tickets = Ticket.objects.filter(reporter=request.user).order_by('-updated_at')
        context = {
            'role_title': 'Functional Analyst',
            'my_projects_count': projects.count(),
            'my_reported_tickets': tickets[:10],
        }
        return render(request, 'dashboard_fa.html', context)'''

new_fa = '''    elif role == 'FA':
        projects = Project.objects.filter(functional_analysts=request.user)
        project_workloads = []
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
        context = {
            'role_title': 'Functional Analyst',
            'my_projects_count': projects.count(),
            'project_workloads': project_workloads,
        }
        return render(request, 'dashboard_fa.html', context)'''

views_content = views_content.replace(old_fa, new_fa)

new_filter_view = '''
@login_required
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
        title += f" in {project.name}"
        
    if developer_id:
        if developer_id == 'none':
            tickets = tickets.filter(assignee__isnull=True)
            title += " (Unassigned)"
        else:
            dev = get_object_or_404(User, pk=developer_id)
            tickets = tickets.filter(assignee=dev)
            title += f" assigned to {dev.username}"
            
    return render(request, 'issues/ticket_filtered_list.html', {
        'tickets': tickets,
        'title': title
    })
'''
if 'def ticket_filtered_list' not in views_content:
    views_content += new_filter_view

with open('issues/views.py', 'w', encoding='utf-8') as f:
    f.write(views_content)


urls_path = 'issues/urls.py'
with open(urls_path, 'r', encoding='utf-8') as f:
    urls_content = f.read()

if 'ticket_filtered_list' not in urls_content:
    urls_content = urls_content.replace(
        "path('tickets/new/', views.ticket_create, name='ticket_create'),",
        "path('tickets/new/', views.ticket_create, name='ticket_create'),\n    path('tickets/filter/', views.ticket_filtered_list, name='ticket_filtered_list'),"
    )
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(urls_content)

dash_fa = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Dashboard</h1>
    <a href="{% url 'ticket_create' %}" class="btn btn-primary btn-header">+ Log New Bug</a>
</div>

<div class="metrics-grid">
    <div class="metric-card">
        <h3>Assigned Projects</h3>
        <div class="value">{{ my_projects_count }}</div>
    </div>
</div>

<h2>Assigned Projects & Developer Workloads</h2>
<p style="color:var(--text-muted); margin-bottom: 24px;">Click the active pending numbers to drill down into the specific issue list.</p>

<div style="display:flex; flex-direction:column; gap:24px;">
    {% for pw in project_workloads %}
    <div style="background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden;">
        <div style="padding: 16px 24px; border-bottom: 1px solid var(--border); background:rgba(255,255,255,0.02); display:flex; justify-content:space-between; align-items:center;">
            <h3 style="margin:0; font-size:18px;">{{ pw.project.name }}</h3>
            <div style="font-weight:600; color:var(--accent-red);">
                Total Pending Points: 
                <a href="{% url 'ticket_filtered_list' %}?project={{ pw.project.pk }}" style="color:var(--accent-red); text-decoration:underline;">{{ pw.total_pending }}</a>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Developer</th>
                    <th>Pending Points (Active Workload)</th>
                </tr>
            </thead>
            <tbody>
                {% for dev in pw.dev_workloads %}
                <tr>
                    <td style="color:var(--text-primary); font-weight:500;">Developer: {{ dev.developer.username }}</td>
                    <td>
                        <a href="{% url 'ticket_filtered_list' %}?project={{ pw.project.pk }}&dev={{ dev.developer.pk }}" style="display:inline-block; padding:4px 12px; background:rgba(59,130,246,0.1); color:var(--accent-blue); border-radius:12px; font-weight:600; text-decoration:none;">
                            {{ dev.pending_count }} items
                        </a>
                    </td>
                </tr>
                {% endfor %}
                {% if pw.unassigned_count > 0 %}
                <tr>
                    <td style="color:var(--text-primary); font-weight:500;">Unassigned</td>
                    <td>
                        <a href="{% url 'ticket_filtered_list' %}?project={{ pw.project.pk }}&dev=none" style="display:inline-block; padding:4px 12px; background:rgba(245,158,11,0.1); color:#f59e0b; border-radius:12px; font-weight:600; text-decoration:none;">
                            {{ pw.unassigned_count }} items
                        </a>
                    </td>
                </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
    {% empty %}
    <div style="text-align:center; padding: 40px; color: var(--text-muted);">You don't have any assigned projects yet.</div>
    {% endfor %}
</div>
{% endblock %}
'''
with open('templates/dashboard_fa.html', 'w', encoding='utf-8') as f:
    f.write(dash_fa)

filter_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
    <h1>{{ title }}</h1>
    <a href="{% url 'dashboard' %}" class="btn" style="background:var(--bg-card); color:var(--text-primary);">← Back to Dashboard</a>
</div>

<div style="background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden;">
    <table>
        <thead>
            <tr>
                <th>ISSUE-#</th>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Assignee</th>
                <th>Created</th>
            </tr>
        </thead>
        <tbody>
            {% for t in tickets %}
            <tr>
                <td style="color: var(--text-muted); font-family: monospace;">#{{ t.pk }}</td>
                <td><a href="{% url 'ticket_detail' t.pk %}" style="color: var(--text-primary); text-decoration: none; font-weight: 500;">{{ t.title }}</a></td>
                <td><span class="badge badge-STATUS-{{ t.status }}">{{ t.get_status_display }}</span></td>
                <td><span class="badge badge-PRIORITY-{{ t.priority }}">{{ t.get_priority_display }}</span></td>
                <td style="color: var(--text-muted);">{{ t.assignee.username|default:"Unassigned" }}</td>
                <td style="color: var(--text-muted); font-size: 14px;">{{ t.created_at|date:"M d, Y" }}</td>
            </tr>
            {% empty %}
            <tr><td colspan="6" style="text-align:center; padding: 40px; color:var(--text-muted);">No pending points match this filter!</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''
with open('templates/issues/ticket_filtered_list.html', 'w', encoding='utf-8') as f:
    f.write(filter_html)

print("Phase 5 Views and UI built.")

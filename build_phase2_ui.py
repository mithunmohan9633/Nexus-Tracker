import os

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Base has already been created, we just need to adapt the dashboards.

# dashboard_pm.html
pm_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Dashboard</h1>
    <a href="{% url 'project_create' %}" class="btn btn-primary btn-header">+ New Project</a>
</div>
<div class="metrics-grid">
    <div class="metric-card"><h3>Total Projects</h3><div class="value">{{ projects_count }}</div></div>
    <div class="metric-card" style="border-color: var(--accent-red);"><h3 style="color: var(--accent-red);">System Open Bugs</h3><div class="value">{{ open_tickets }}</div></div>
    <div class="metric-card" style="border-color: var(--accent-green);"><h3 style="color: var(--accent-green);">Closed Bugs</h3><div class="value">{{ closed_tickets }}</div></div>
</div>
<h2>Recent Projects</h2>
<table>
    <tr><th>Project Name</th><th>Manager / APM</th><th>Created</th></tr>
    {% for p in recent_projects %}
    <tr><td>{{ p.name }}</td><td>{{ p.apm.username|default:"Unassigned" }}</td><td>{{ p.created_at|date:"M d, Y" }}</td></tr>
    {% endfor %}
</table>
{% endblock %}
'''
write_file('templates/dashboard_pm.html', pm_html)

# dashboard_apm.html
apm_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Dashboard</h1>
    <a href="{% url 'project_create' %}" class="btn btn-primary btn-header">+ Create Project Team</a>
</div>
<h2>Projects Assigned to You</h2>
<table>
    <tr><th>Project Name</th><th>Team Size</th><th>Bugs</th></tr>
    {% for p in my_projects %}
    <tr><td>{{ p.name }}</td><td>{{ p.team.count }} Members</td><td>{{ p.tickets.count }} Tickets</td></tr>
    {% empty %}
    <tr><td colspan="3" style="text-align:center;">No projects assigned yet.</td></tr>
    {% endfor %}
</table>
{% endblock %}
'''
write_file('templates/dashboard_apm.html', apm_html)

# dashboard_fa.html
fa_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Dashboard</h1>
    <a href="{% url 'ticket_create' %}" class="btn btn-primary btn-header">+ Log New Bug</a>
</div>
<div class="metrics-grid">
    <div class="metric-card"><h3>Assigned Projects</h3><div class="value">{{ my_projects_count }}</div></div>
</div>
<h2>Bugs Logged By You</h2>
<table>
    <tr><th>Ticket</th><th>Project</th><th>Status</th><th>Dev Assigned</th></tr>
    {% for t in my_reported_tickets %}
    <tr>
        <td><a href="{% url 'ticket_detail' t.pk %}" style="color:var(--text-primary);">{{ t.title }}</a></td>
        <td>{{ t.project.name }}</td>
        <td><span class="badge badge-STATUS-{{ t.status }}">{{ t.get_status_display }}</span></td>
        <td>{{ t.assignee.username|default:"None" }}</td>
    </tr>
    {% empty %}
    <tr><td colspan="4" style="text-align:center;">You haven't logged any bugs yet.</td></tr>
    {% endfor %}
</table>
{% endblock %}
'''
write_file('templates/dashboard_fa.html', fa_html)

# dashboard_dev.html
dev_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Workspace</h1>
</div>
<h2>Your Open Tasks</h2>
<table>
    <tr><th>Ticket</th><th>Project</th><th>Priority</th><th>Time Est.</th><th>Action</th></tr>
    {% for t in open_tasks %}
    <tr>
        <td><a href="{% url 'ticket_detail' t.pk %}" style="color:var(--text-primary);">{{ t.title }}</a></td>
        <td>{{ t.project.name }}</td>
        <td><span class="badge badge-PRIORITY-{{ t.priority }}">{{ t.get_priority_display }}</span></td>
        <td>{{ t.estimated_time_hours|default:"?" }} hrs</td>
        <td><a href="{% url 'ticket_detail' t.pk %}" class="btn" style="background:#334155; padding:6px 12px; font-size:12px;">View & Resolve</a></td>
    </tr>
    {% empty %}
    <tr><td colspan="5" style="text-align:center;">You have no open tasks. Great job!</td></tr>
    {% endfor %}
</table>
{% endblock %}
'''
write_file('templates/dashboard_dev.html', dev_html)

# generic_form.html
form_html = '''{% extends 'base.html' %}
{% block content %}
<h1>{{ title }}</h1>
<div style="background: var(--bg-card); padding: 32px; border-radius: var(--radius); border: 1px solid var(--border); max-width: 600px; margin-top: 24px;">
    <form method="post">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
            <label>{{ field.label }}</label>
            {{ field }}
        </div>
        {% endfor %}
        <button type="submit" class="btn btn-primary" style="margin-top: 16px;">Save</button>
    </form>
</div>
{% endblock %}
'''
write_file('templates/issues/generic_form.html', form_html)

# ticket_detail.html
detail_html = '''{% extends 'base.html' %}
{% block content %}
<div style="margin-bottom: 24px;">
    <h1 style="margin-bottom:8px;">{{ ticket.title }}</h1>
    <div style="color:var(--text-muted); font-size:14px;">Project: {{ ticket.project.name }} | Priority: {{ ticket.get_priority_display }} | Time: {{ ticket.estimated_time_hours }} hrs</div>
    <div style="margin-top:16px; padding:16px; background:var(--bg-card); border-radius:var(--radius); border:1px solid var(--border);">{{ ticket.description }}</div>
</div>

<div style="display: flex; gap: 32px;">
    <div style="flex: 2;">
        <h2>Remarks Timeline</h2>
        <div style="margin-top:16px;">
            {% for r in ticket.remarks.all %}
            <div style="padding:16px; background:rgba(255,255,255,0.03); border-radius:var(--radius); margin-bottom:12px;">
                <div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">{{ r.author.username }} ({{ r.author.profile.get_role_display }}) • {{ r.created_at|date:"M d g:i a" }}</div>
                <div>{{ r.text }}</div>
            </div>
            {% empty %}
            <p style="color:var(--text-muted);">No remarks yet.</p>
            {% endfor %}
        </div>
        
        <div style="margin-top: 24px;">
            <form method="post">
                {% csrf_token %}
                {{ remark_form.text }}
                <button type="submit" name="add_remark" class="btn btn-primary" style="margin-top: 8px; width:auto;">Add Remark</button>
            </form>
        </div>
    </div>
    
    <div style="flex: 1;">
        {% if role == 'DEV' %}
        <div style="background:var(--bg-card); padding:24px; border-radius:var(--radius); border:1px solid var(--border);">
            <h3>Update Status</h3>
            <form method="post" style="margin-top:16px;">
                {% csrf_token %}
                <div class="form-group">{{ status_form.status }}</div>
                <button type="submit" name="update_status" class="btn btn-primary">Change Status</button>
            </form>
        </div>
        {% else %}
        <div style="background:var(--bg-card); padding:24px; border-radius:var(--radius); border:1px solid var(--border);">
            <h3>Current Status</h3>
            <div style="margin-top:16px;"><span class="badge badge-STATUS-{{ ticket.status }}" style="font-size:16px;">{{ ticket.get_status_display }}</span></div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
'''
write_file('templates/issues/ticket_detail.html', detail_html)

print("Phase 2 UI implemented.")

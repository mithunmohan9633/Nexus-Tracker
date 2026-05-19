import os

hr_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Dashboard</h1>
    <a href="{% url 'employee_create' %}" class="btn btn-primary btn-header" style="background: var(--accent-green);">+ Add Employee</a>
</div>

<div class="metrics-grid">
    <div class="metric-card" style="border-color: var(--accent-green);">
        <h3 style="color: var(--accent-green);">Total Active Employees</h3>
        <div class="value">{{ total_employees }}</div>
    </div>
    <div class="metric-card">
        <h3>Total Active Projects</h3>
        <div class="value">{{ projects_count }}</div>
    </div>
</div>

<h2>Company Directory</h2>
<div style="background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; margin-top: 16px;">
    <table>
        <thead>
            <tr>
                <th>Username</th>
                <th>Assigned Role</th>
                <th>System ID</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            {% for emp in employees %}
            <tr>
                <td style="color: var(--text-primary); font-weight: 500;">{{ emp.user.username }}</td>
                <td>{{ emp.get_role_display }}</td>
                <td style="color: var(--text-muted); font-family: monospace;">#{{ emp.user.id }}</td>
                <td>
                    {% if not emp.user.is_superuser %}
                    <form action="{% url 'employee_delete' emp.user.pk %}" method="post" style="display:inline;" onsubmit="return confirm('Are you sure you want to permanently delete this employee?');">
                        {% csrf_token %}
                        <button type="submit" class="btn" style="background:var(--accent-red); color:white; padding:6px 12px; font-size:12px;">Delete</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% empty %}
            <tr><td colspan="4" style="text-align:center; color: var(--text-muted); padding: 40px;">No employees provisioned yet.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''

with open('templates/dashboard_hr.html', 'w', encoding='utf-8') as f:
    f.write(hr_html)

apm_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Dashboard</h1>
    <!-- APM cannot create projects directly anymore. PM does it. -->
</div>
<h2>Projects Delegated to You</h2>
<p style="color:var(--text-muted); margin-bottom: 16px;">These projects were assigned to you by a Project Manager. Click 'Manage Team' to assign Analysts and Developers.</p>
<table>
    <tr><th>Project Name</th><th>Analysts</th><th>Developers</th><th>Bugs</th><th>Action</th></tr>
    {% for p in my_projects %}
    <tr>
        <td>{{ p.name }}</td>
        <td>{{ p.functional_analysts.count }} FAs</td>
        <td>{{ p.developers.count }} Devs</td>
        <td>{{ p.tickets.count }} Tickets</td>
        <td><a href="{% url 'project_edit_team' p.pk %}" class="btn btn-primary" style="padding:6px 12px; font-size:12px;">Manage Team</a></td>
    </tr>
    {% empty %}
    <tr><td colspan="5" style="text-align:center;">No projects assigned yet. Wait for a Project Manager to delegate one.</td></tr>
    {% endfor %}
</table>
{% endblock %}
'''

with open('templates/dashboard_apm.html', 'w', encoding='utf-8') as f:
    f.write(apm_html)

print("HR and APM dashboards updated.")

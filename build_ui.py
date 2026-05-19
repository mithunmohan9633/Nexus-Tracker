import os

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# CSS
style_css = '''
:root {
    --bg-dark: #0f172a;
    --bg-card: #1e293b;
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
    --accent-red: #ef4444;
    --accent-blue: #3b82f6;
    --accent-green: #10b981;
    --accent-purple: #8b5cf6;
    --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --border: #334155;
    --radius: 12px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background-color: var(--bg-dark);
    color: var(--text-primary);
    font-family: 'Inter', -apple-system, sans-serif;
    line-height: 1.6;
    display: flex;
    min-height: 100vh;
}

/* Sidebar */
.sidebar {
    width: 260px;
    background-color: var(--bg-card);
    border-right: 1px solid var(--border);
    padding: 24px;
    display: flex;
    flex-direction: column;
}

.logo { font-size: 24px; font-weight: 800; color: var(--accent-blue); margin-bottom: 40px; letter-spacing: -0.5px;}

.nav-link {
    color: var(--text-muted);
    text-decoration: none;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.nav-link:hover, .nav-link.active {
    background-color: rgb(59 130 246 / 0.1);
    color: var(--accent-blue);
    transform: translateX(4px);
}

.main-content {
    flex: 1;
    padding: 48px;
    overflow-y: auto;
}

/* Cards */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 24px;
    margin-bottom: 40px;
}

.metric-card {
    background: var(--bg-card);
    padding: 24px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.2);
    border-color: var(--accent-blue);
}

.metric-card h3 { color: var(--text-muted); font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
.metric-card .value { font-size: 36px; font-weight: 700; margin-top: 8px; color: var(--text-primary); }

/* Glassmorphism Login */
.login-container {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100vw;
    height: 100vh;
    background: radial-gradient(circle at top right, #1e1b4b, var(--bg-dark));
}

.login-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(16px);
    padding: 48px;
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    width: 100%;
    max-width: 420px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    text-align: center;
}

/* Forms & Inputs */
.form-group { margin-bottom: 24px; text-align: left; }
.form-group label { display: block; margin-bottom: 8px; color: var(--text-muted); font-size: 14px; font-weight: 500; }
.form-input {
    width: 100%;
    padding: 12px 16px;
    background: var(--bg-dark);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-primary);
    font-family: inherit;
    font-size: 15px;
    transition: border-color 0.2s;
}
.form-input:focus { outline: none; border-color: var(--accent-blue); }

.btn {
    display: inline-block;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}
.btn-primary {
    background: var(--accent-blue);
    color: white;
    width: 100%;
}
.btn-primary:hover { background: #2563eb; transform: scale(1.02); }

.btn-header { width: auto; background: var(--accent-purple); float: right;}

/* Tables */
table { width: 100%; border-collapse: collapse; margin-top: 24px; }
th, td { padding: 16px; text-align: left; border-bottom: 1px solid var(--border); }
th { color: var(--text-muted); font-weight: 600; font-size: 13px; text-transform: uppercase; }
tr:hover td { background-color: rgba(255,255,255,0.02); }

.badge { padding: 4px 10px; border-radius: 99px; font-size: 12px; font-weight: 600; }
.badge-PRIORITY-CRITICAL { background: rgb(239 68 68 / 0.2); color: var(--accent-red); }
.badge-PRIORITY-HIGH { background: rgb(245 158 11 / 0.2); color: #f59e0b; }
.badge-STATUS-IN_PROGRESS { background: rgb(59 130 246 / 0.2); color: var(--accent-blue); }
.badge-STATUS-TODO { background: rgb(148 163 184 / 0.2); color: var(--text-muted); }
.badge-STATUS-DONE { background: rgb(16 185 129 / 0.2); color: var(--accent-green); }
'''
write_file('static/css/style.css', style_css)

# base.html 
base_html = '''{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Tracker</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    {% if user.is_authenticated %}
    <nav class="sidebar">
        <div class="logo">NexusTracker</div>
        <a href="{% url 'dashboard' %}" class="nav-link">Dashboard</a>
        <a href="{% url 'ticket_list' %}" class="nav-link">All Tickets</a>
        <div style="flex-grow: 1;"></div>
        <div style="color: var(--text-muted); margin-bottom: 16px; font-size: 14px;">User: {{ user.username }}</div>
        <form action="{% url 'logout' %}" method="post">
            {% csrf_token %}
            <button type="submit" class="nav-link" style="background:none; border:none; width:100%; text-align:left; cursor:pointer;">Log out</button>
        </form>
    </nav>
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    {% else %}
        {% block login %}{% endblock %}
    {% endif %}
</body>
</html>
'''
write_file('templates/base.html', base_html)

# login.html
login_html = '''{% extends 'base.html' %}
{% block login %}
<div class="login-container">
    <div class="login-card">
        <div class="logo" style="margin-bottom: 24px; font-size: 32px;">NexusTracker</div>
        <p style="color: var(--text-muted); margin-bottom: 32px;">Sign in to your workspace</p>
        
        <form method="post">
            {% csrf_token %}
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" class="form-input" required>
            </div>
            <div class="form-group" style="margin-bottom: 32px;">
                <label>Password</label>
                <input type="password" name="password" class="form-input" required>
            </div>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
    </div>
</div>
{% endblock %}
'''
write_file('templates/registration/login.html', login_html)

# dashboard.html
dashboard_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>Dashboard</h1>
    <a href="{% url 'ticket_create' %}" class="btn btn-primary btn-header">+ New Issue</a>
</div>

<div class="metrics-grid">
    <div class="metric-card">
        <h3>Open Issues</h3>
        <div class="value">{{ total_open }}</div>
    </div>
    <div class="metric-card" style="border-color: var(--accent-purple);">
        <h3 style="color: var(--accent-purple);">Assigned to Me</h3>
        <div class="value">{{ my_tickets_count }}</div>
    </div>
    <div class="metric-card">
        <h3>Team Members</h3>
        <div class="value">Active</div>
    </div>
</div>

<h2 style="margin-bottom: 16px;">Recently Active</h2>
<div style="background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden;">
    <table>
        <thead>
            <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Assignee</th>
                <th>Updated</th>
            </tr>
        </thead>
        <tbody>
            {% for t in recent_tickets %}
            <tr>
                <td><a href="{% url 'ticket_update' t.pk %}" style="color: var(--text-primary); text-decoration: none; font-weight: 500;">{{ t.title }}</a></td>
                <td><span class="badge badge-STATUS-{{ t.status }}">{{ t.get_status_display }}</span></td>
                <td><span class="badge badge-PRIORITY-{{ t.priority }}">{{ t.get_priority_display }}</span></td>
                <td style="color: var(--text-muted);">{{ t.assignee.username|default:"Unassigned" }}</td>
                <td style="color: var(--text-muted); font-size: 14px;">{{ t.updated_at|date:"M d, Y" }}</td>
            </tr>
            {% empty %}
            <tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 40px;">No tickets found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''
write_file('templates/dashboard.html', dashboard_html)

# ticket_form.html
form_html = '''{% extends 'base.html' %}
{% block content %}
<h1>{{ action }} Issue</h1>
<p style="color: var(--text-muted); margin-bottom: 32px;">Fill out the details below to log a new tracker item.</p>

<div style="background: var(--bg-card); padding: 32px; border-radius: var(--radius); border: 1px solid var(--border); max-width: 600px;">
    <form method="post">
        {% csrf_token %}
        <div class="form-group">
            <label>Issue Title</label>
            {{ form.title }}
        </div>
        
        <div class="form-group">
            <label>Priority Level</label>
            {{ form.priority }}
        </div>

        {% if action == 'Update' %}
        <div class="form-group">
            <label>Status</label>
            <select name="status" class="form-input">
                <option value="TODO" {% if ticket.status == 'TODO' %}selected{% endif %}>To Do</option>
                <option value="IN_PROGRESS" {% if ticket.status == 'IN_PROGRESS' %}selected{% endif %}>In Progress</option>
                <option value="IN_REVIEW" {% if ticket.status == 'IN_REVIEW' %}selected{% endif %}>In Review</option>
                <option value="DONE" {% if ticket.status == 'DONE' %}selected{% endif %}>Done</option>
            </select>
        </div>
        {% endif %}
        
        <div class="form-group">
            <label>Description</label>
            {{ form.description }}
        </div>
        
        <button type="submit" class="btn btn-primary" style="margin-top: 16px;">Save Issue</button>
    </form>
</div>
{% endblock %}
'''
write_file('templates/issues/ticket_form.html', form_html)

# ticket_list.html
list_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>All Issues</h1>
    <a href="{% url 'ticket_create' %}" class="btn btn-primary btn-header">+ New Issue</a>
</div>

<div style="background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden;">
    <table>
        <thead>
            <tr>
                <th>ISSUE-#</th>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Reporter</th>
                <th>Created</th>
            </tr>
        </thead>
        <tbody>
            {% for t in tickets %}
            <tr>
                <td style="color: var(--text-muted); font-family: monospace;">#{{ t.pk }}</td>
                <td><a href="{% url 'ticket_update' t.pk %}" style="color: var(--text-primary); text-decoration: none; font-weight: 500;">{{ t.title }}</a></td>
                <td><span class="badge badge-STATUS-{{ t.status }}">{{ t.get_status_display }}</span></td>
                <td><span class="badge badge-PRIORITY-{{ t.priority }}">{{ t.get_priority_display }}</span></td>
                <td style="color: var(--text-muted);">{{ t.reporter.username }}</td>
                <td style="color: var(--text-muted); font-size: 14px;">{{ t.created_at|date:"M d, Y" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''
write_file('templates/issues/ticket_list.html', list_html)
print("UI files generated successfully.")

import os

# 1. Developer Dashboard with verification states
dev_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Workspace</h1>
</div>

{% if pending_review_tasks %}
<div style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.3); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 32px;">
    <h3 style="margin:0 0 4px 0; color: #f59e0b;">⏳ Awaiting FA Verification ({{ pending_review_tasks.count }})</h3>
    <p style="margin:0; color:var(--text-muted); font-size:14px;">These tasks have been submitted for review. You will be notified if they are returned.</p>
    <table style="margin-top:16px;">
        <tr><th>Ticket</th><th>Project</th><th>Submitted</th></tr>
        {% for t in pending_review_tasks %}
        <tr>
            <td><a href="{% url 'ticket_detail' t.pk %}" style="color:var(--text-primary);">{{ t.title }}</a></td>
            <td style="color:var(--text-muted);">{{ t.project.name }}</td>
            <td style="color:var(--text-muted); font-size:13px;">{{ t.updated_at|date:"M d, g:i a" }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
{% endif %}

<h2>Your Open Tasks</h2>
<div style="background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; margin-top: 16px;">
    <table>
        <thead>
            <tr><th>ISSUE-#</th><th>Title</th><th>Project</th><th>Priority</th><th>Est. Time</th><th>Action</th></tr>
        </thead>
        <tbody>
            {% for t in open_tasks %}
            <tr>
                <td style="color:var(--text-muted); font-family:monospace;">#{{ t.pk }}</td>
                <td><a href="{% url 'ticket_detail' t.pk %}" style="color:var(--text-primary); font-weight:500;">{{ t.title }}</a></td>
                <td style="color:var(--text-muted);">{{ t.project.name }}</td>
                <td><span class="badge badge-PRIORITY-{{ t.priority }}">{{ t.get_priority_display }}</span></td>
                <td>{{ t.estimated_time_hours|default:"?" }} hrs</td>
                <td><a href="{% url 'ticket_detail' t.pk %}" class="btn" style="background:#334155; padding:6px 12px; font-size:12px;">Open &amp; Resolve</a></td>
            </tr>
            {% empty %}
            <tr><td colspan="6" style="text-align:center; padding:40px; color:var(--text-muted);">🎉 All clear! No open tasks assigned.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''
with open('templates/dashboard_dev.html', 'w', encoding='utf-8') as f:
    f.write(dev_html)

# 2. FA Dashboard with Verification Panel
with open('templates/dashboard_fa.html', 'r', encoding='utf-8') as f:
    fa_html = f.read()

verification_panel = '''
{% if verification_count > 0 %}
<div style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.4); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 32px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <h3 style="margin:0; color:#f59e0b;">🔍 Pending Your Verification ({{ verification_count }})</h3>
    </div>
    <table>
        <thead>
            <tr><th>ISSUE-#</th><th>Title</th><th>Project</th><th>Developer</th><th>Action</th></tr>
        </thead>
        <tbody>
            {% for t in verification_tickets %}
            <tr>
                <td style="color:var(--text-muted); font-family:monospace; font-size:13px;">#{{ t.pk }}</td>
                <td style="color:var(--text-primary); font-weight:500;">{{ t.title }}</td>
                <td style="color:var(--text-muted);">{{ t.project.name }}</td>
                <td>{{ t.assignee.username|default:"Unassigned" }}</td>
                <td>
                    <div style="display:flex; gap:8px;">
                        <form action="{% url 'ticket_verify' t.pk %}" method="post" style="display:inline;">
                            {% csrf_token %}
                            <button type="submit" name="action" value="approve" class="btn" style="background:var(--accent-green); color:white; padding:5px 12px; font-size:12px;">✓ Approve</button>
                        </form>
                        <a href="{% url 'ticket_detail' t.pk %}#reject" class="btn" style="background:var(--accent-red); color:white; padding:5px 12px; font-size:12px;">✗ Reject</a>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

'''

# Insert panel before project workloads heading
fa_html = fa_html.replace('<h2>Your Assigned Projects</h2>', verification_panel + '<h2>Your Assigned Projects</h2>')
with open('templates/dashboard_fa.html', 'w', encoding='utf-8') as f:
    f.write(fa_html)

# 3. Update ticket_detail.html to handle DEV submit-for-review and FA reject form
with open('templates/issues/ticket_detail.html', 'r', encoding='utf-8') as f:
    detail_html = f.read()

# Replace the old dev status panel
old_dev_panel = '''        {% if role == 'DEV' %}
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
        {% endif %}'''

new_dev_panel = '''        <div style="background:var(--bg-card); padding:24px; border-radius:var(--radius); border:1px solid var(--border);">
            <h3>Status</h3>
            <div style="margin-top:16px; margin-bottom:20px;"><span class="badge badge-STATUS-{{ ticket.status }}" style="font-size:15px; padding:6px 14px;">{{ ticket.get_status_display }}</span></div>
            
            {% if role == 'DEV' and ticket.status != 'DONE' and ticket.status != 'PENDING_REVIEW' %}
            <form method="post" style="margin-top:8px;">
                {% csrf_token %}
                <select name="status" class="form-input" style="margin-bottom:10px;">
                    <option value="IN_PROGRESS" {% if ticket.status == 'IN_PROGRESS' %}selected{% endif %}>In Progress</option>
                    <option value="PENDING_REVIEW">Submit for FA Review</option>
                </select>
                <button type="submit" name="update_status" class="btn btn-primary" style="width:100%;">Update Status</button>
            </form>
            {% elif role == 'DEV' and ticket.status == 'PENDING_REVIEW' %}
            <p style="color:#f59e0b; font-size:13px;">⏳ Awaiting Functional Analyst verification.</p>
            {% endif %}
            
            {% if role == 'FA' and ticket.status == 'PENDING_REVIEW' %}
            <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--border);" id="reject">
                <h4 style="margin-top:0; color:var(--accent-green);">Verify This Fix</h4>
                <form action="{% url 'ticket_verify' ticket.pk %}" method="post">
                    {% csrf_token %}
                    <button type="submit" name="action" value="approve" class="btn" style="background:var(--accent-green); color:white; width:100%; margin-bottom:12px;">✓ Approve & Close Bug</button>
                    <textarea name="rejection_reason" class="form-input" rows="2" placeholder="Rejection reason (required if rejecting)..." style="margin-bottom:8px;"></textarea>
                    <button type="submit" name="action" value="reject" class="btn" style="background:var(--accent-red); color:white; width:100%;">✗ Reject & Return to Dev</button>
                </form>
            </div>
            {% endif %}
        </div>'''

detail_html = detail_html.replace(old_dev_panel, new_dev_panel)

# Also update system remark styling in timeline
old_remark = '''            {% for r in ticket.remarks.all %}
            <div style="padding:16px; background:rgba(255,255,255,0.03); border-radius:var(--radius); margin-bottom:12px;">
                <div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">{{ r.author.username }} ({{ r.author.profile.get_role_display }}) • {{ r.created_at|date:"M d g:i a" }}</div>
                <div style="white-space: pre-wrap;">{{ r.text }}</div>
            </div>'''

new_remark = '''            {% for r in ticket.remarks.all %}
            <div style="padding:16px; background:{% if r.is_system %}rgba(245,158,11,0.06){% else %}rgba(255,255,255,0.03){% endif %}; border-radius:var(--radius); margin-bottom:12px; border-left: 3px solid {% if r.is_system %}#f59e0b{% else %}transparent{% endif %};">
                <div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">
                    {% if r.is_system %}🔔 System{% else %}{{ r.author.username }} ({{ r.author.profile.get_role_display }}){% endif %} • {{ r.created_at|date:"M d g:i a" }}
                </div>
                <div style="white-space: pre-wrap;">{{ r.text }}</div>
            </div>'''

detail_html = detail_html.replace(old_remark, new_remark)
with open('templates/issues/ticket_detail.html', 'w', encoding='utf-8') as f:
    f.write(detail_html)

# 4. Build dedicated ticket form template (replaces generic_form for tickets)
ticket_form_html = '''{% extends 'base.html' %}
{% block content %}
<h1 style="margin-bottom:8px;">{{ title }}</h1>
<p style="color:var(--text-muted); margin-bottom:32px;">Fill in the details below. All QA fields ensure developers can reproduce and fix this issue quickly.</p>

<div style="background: var(--bg-card); padding: 32px; border-radius: var(--radius); border: 1px solid var(--border);">
    <form method="post">
        {% csrf_token %}
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
            <div class="form-group" style="grid-column: span 2;">
                <label>Issue Title *</label>
                {{ form.title }}
            </div>
            <div class="form-group">
                <label>Module</label>
                {{ form.modules }}
            </div>
            <div class="form-group">
                <label>Issue Identified Date</label>
                {{ form.issue_identified_date }}
            </div>
            <div class="form-group" style="grid-column: span 2;">
                <label>Path (URL / File Path)</label>
                {{ form.path }}
            </div>
            <div class="form-group" style="grid-column: span 2;">
                <label style="color:var(--accent-red);">Current Behaviour *</label>
                {{ form.current_behaviour }}
            </div>
            <div class="form-group" style="grid-column: span 2;">
                <label style="color:var(--accent-green);">Expected Behaviour *</label>
                {{ form.expected_behaviour }}
            </div>
            <div class="form-group" style="grid-column: span 2;">
                <label>Examples / Steps to Reproduce</label>
                {{ form.examples }}
            </div>
            <div class="form-group" style="grid-column: span 2;">
                <label>API / Other Data</label>
                {{ form.api_or_other_datas }}
            </div>
            <div class="form-group">
                <label>Priority</label>
                {{ form.priority }}
            </div>
            <div class="form-group">
                <label>Estimated Time (hrs)</label>
                {{ form.estimated_time_hours }}
            </div>
            <div class="form-group" style="grid-column: span 2;">
                <label>Assign to Developer</label>
                {{ form.assignee }}
            </div>
        </div>
        <div style="margin-top:24px; display:flex; gap:12px;">
            <button type="submit" class="btn btn-primary">Log Issue</button>
            <a href="{% url 'dashboard' %}" class="btn" style="background:var(--bg-card); color:var(--text-muted);">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
'''
with open('templates/issues/ticket_form.html', 'w', encoding='utf-8') as f:
    f.write(ticket_form_html)

print("All Phase 7 UI templates complete!")

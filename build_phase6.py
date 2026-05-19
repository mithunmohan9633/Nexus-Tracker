import os
import django

# Clean up existing tickets before migration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bug_tracker.settings')
django.setup()
from issues.models import Ticket, TicketRemark
Ticket.objects.all().delete()
TicketRemark.objects.all().delete()

# 1. Update Models
models_py = '''from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('PM', 'Project Manager'),
        ('APM', 'Assistant Project Manager'),
        ('FA', 'Functional Analyst'),
        ('DEV', 'Developer'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='DEV')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    apm = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects', limit_choices_to={'profile__role': 'APM'})
    functional_analysts = models.ManyToManyField(User, related_name='assigned_fa_projects', blank=True, limit_choices_to={'profile__role': 'FA'})
    developers = models.ManyToManyField(User, related_name='assigned_dev_projects', blank=True, limit_choices_to={'profile__role': 'DEV'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review'),
        ('DONE', 'Done'),
    )
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=200)
    
    # New QA Fields instead of description
    modules = models.CharField(max_length=200, blank=True, null=True)
    issue_identified_date = models.DateField(blank=True, null=True)
    path = models.CharField(max_length=500, blank=True, null=True)
    current_behaviour = models.TextField(blank=True, null=True)
    expected_behaviour = models.TextField(blank=True, null=True)
    examples = models.TextField(blank=True, null=True)
    api_or_other_datas = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    estimated_time_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_tickets')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'profile__role': 'DEV'})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.pk} {self.title}"

class TicketRemark(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='remarks')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Remark by {self.author.username} on {self.ticket}"
'''
with open('issues/models.py', 'w', encoding='utf-8') as f:
    f.write(models_py)

# 2. Update Forms
with open('issues/forms.py', 'r', encoding='utf-8') as f:
    forms_py = f.read()

import re
old_ticket_form = re.search(r'class TicketForm.*?def __init__.*?\n', forms_py, re.DOTALL | re.MULTILINE)

new_ticket_form = '''class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'modules', 'issue_identified_date', 'path', 'current_behaviour', 'expected_behaviour', 'examples', 'api_or_other_datas', 'priority', 'assignee', 'estimated_time_hours']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'modules': forms.TextInput(attrs={'class': 'form-input'}),
            'issue_identified_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'path': forms.TextInput(attrs={'class': 'form-input'}),
            'current_behaviour': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'expected_behaviour': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'examples': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'api_or_other_datas': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'assignee': forms.Select(attrs={'class': 'form-input'}),
            'estimated_time_hours': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignee'].queryset = User.objects.filter(profile__role='DEV')

def dummy'''

forms_py = re.sub(r'class TicketForm\(forms\.ModelForm\):[\s\S]*?class RemarkForm', new_ticket_form.replace('def dummy', 'class RemarkForm'), forms_py)

with open('issues/forms.py', 'w', encoding='utf-8') as f:
    f.write(forms_py)


# 3. Update Views routing
with open('issues/views.py', 'r', encoding='utf-8') as f:
    views_py = f.read()

old_create = '''@login_required
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
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Create Issue'})'''

new_create = '''@login_required
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
    return render(request, 'issues/generic_form.html', {'form': form, 'title': f'Log Issue for {project.name}'})'''

views_py = views_py.replace(old_create, new_create)
with open('issues/views.py', 'w', encoding='utf-8') as f:
    f.write(views_py)


# 4. Dashboard FA Update
with open('templates/dashboard_fa.html', 'r', encoding='utf-8') as f:
    fa_html = f.read()

fa_html = fa_html.replace('<a href="{% url \'ticket_create\' %}" class="btn btn-primary btn-header">+ Log New Bug</a>', '')
fa_html = fa_html.replace('<h2>Assigned Projects & Developer Workloads</h2>', '<h2>Your Assigned Projects</h2>')

old_header = '''<h3 style="margin:0; font-size:18px;">{{ pw.project.name }}</h3>
            <div style="font-weight:600; color:var(--accent-red);">'''
new_header = '''<div style="display:flex; align-items:center;">
                <h3 style="margin:0; font-size:18px; margin-right:24px;">{{ pw.project.name }}</h3>
                <a href="{% url 'ticket_create' %}?project={{ pw.project.pk }}" class="btn btn-primary" style="padding: 6px 12px; font-size: 13px;">+ Log Bug</a>
            </div>
            <div style="font-weight:600; color:var(--accent-red);">'''
fa_html = fa_html.replace(old_header, new_header)

with open('templates/dashboard_fa.html', 'w', encoding='utf-8') as f:
    f.write(fa_html)

# 5. Ticket Detail Update
detail_html = '''{% extends 'base.html' %}
{% block content %}
<div style="margin-bottom: 24px;">
    <h1 style="margin-bottom:8px;">{{ ticket.title }}</h1>
    <div style="color:var(--text-muted); font-size:14px; margin-bottom: 24px;">
        Project: {{ ticket.project.name }} | Priority: {{ ticket.get_priority_display }} | Assignee: {{ ticket.assignee.username|default:"Unassigned" }}
    </div>

    <!-- Advanced QA Properties Grid -->
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
        <div style="background:var(--bg-card); padding:16px; border-radius:var(--radius); border:1px solid var(--border);">
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase;">Modules</div>
            <div style="font-weight:500;">{{ ticket.modules|default:"N/A" }}</div>
        </div>
        <div style="background:var(--bg-card); padding:16px; border-radius:var(--radius); border:1px solid var(--border);">
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase;">Identified Date</div>
            <div style="font-weight:500;">{{ ticket.issue_identified_date|date:"N j, Y"|default:"N/A" }}</div>
        </div>
        <div style="background:var(--bg-card); padding:16px; border-radius:var(--radius); border:1px solid var(--border); grid-column: span 2;">
            <div style="font-size:12px; color:var(--text-muted); text-transform:uppercase;">Path</div>
            <div style="font-family:monospace; color:var(--accent-blue);">{{ ticket.path|default:"N/A" }}</div>
        </div>
    </div>

    <div style="display:flex; flex-direction:column; gap:16px;">
        <div style="background:var(--bg-card); padding:20px; border-radius:var(--radius); border:1px solid var(--border);">
            <h4 style="margin-top:0; color:var(--accent-red);">Current Behaviour</h4>
            <div style="white-space: pre-wrap;">{{ ticket.current_behaviour|default:"No description provided." }}</div>
        </div>
        <div style="background:var(--bg-card); padding:20px; border-radius:var(--radius); border:1px solid var(--border);">
            <h4 style="margin-top:0; color:var(--accent-green);">Expected Behaviour</h4>
            <div style="white-space: pre-wrap;">{{ ticket.expected_behaviour|default:"No description provided." }}</div>
        </div>
        <div style="background:var(--bg-card); padding:20px; border-radius:var(--radius); border:1px solid var(--border);">
            <h4 style="margin-top:0;">Examples / Reproducibility</h4>
            <div style="white-space: pre-wrap;">{{ ticket.examples|default:"N/A" }}</div>
        </div>
        <div style="background:var(--bg-card); padding:20px; border-radius:var(--radius); border:1px solid var(--border);">
            <h4 style="margin-top:0;">API / Other Data</h4>
            <div style="white-space: pre-wrap; font-family:monospace; font-size:13px;">{{ ticket.api_or_other_datas|default:"N/A" }}</div>
        </div>
    </div>
</div>

<div style="display: flex; gap: 32px; margin-top: 40px;">
    <div style="flex: 2;">
        <h2>Remarks Timeline</h2>
        <div style="margin-top:16px;">
            {% for r in ticket.remarks.all %}
            <div style="padding:16px; background:rgba(255,255,255,0.03); border-radius:var(--radius); margin-bottom:12px;">
                <div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">{{ r.author.username }} ({{ r.author.profile.get_role_display }}) • {{ r.created_at|date:"M d g:i a" }}</div>
                <div style="white-space: pre-wrap;">{{ r.text }}</div>
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
with open('templates/issues/ticket_detail.html', 'w', encoding='utf-8') as f:
    f.write(detail_html)

print("Backend execution complete.")

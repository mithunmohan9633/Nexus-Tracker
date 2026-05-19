import os
import shutil

# 1. Write the new models.py
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
    team = models.ManyToManyField(User, related_name='assigned_projects', blank=True)
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
    description = models.TextField()
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

# 2. Update Admin.py
admin_py = '''from django.contrib import admin
from .models import UserProfile, Project, Ticket, TicketRemark

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'apm', 'created_at')
    filter_horizontal = ('team',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'assignee', 'reporter')
    list_filter = ('status', 'priority', 'project')

admin.site.register(TicketRemark)
'''
with open('issues/admin.py', 'w', encoding='utf-8') as f:
    f.write(admin_py)

# 3. Wipe database and migrations to start fresh 
if os.path.exists('db.sqlite3'):
    os.remove('db.sqlite3')

migrations_dir = 'issues/migrations'
if os.path.exists(migrations_dir):
    for filename in os.listdir(migrations_dir):
        if filename != '__init__.py' and filename.endswith('.py'):
            os.remove(os.path.join(migrations_dir, filename))

print("Phase 2 Models Updated and DB wiped.")

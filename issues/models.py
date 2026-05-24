from django.db import models
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
    full_name = models.CharField(max_length=100, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    apm = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects', limit_choices_to={'profile__role': 'APM'})
    functional_analysts = models.ManyToManyField(User, related_name='assigned_fa_projects', blank=True, limit_choices_to={'profile__role': 'FA'})
    developers = models.ManyToManyField(User, related_name='assigned_dev_projects', blank=True, limit_choices_to={'profile__role': 'DEV'})
    deadline = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    delete_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('PENDING_REVIEW', 'Pending FA Review'),
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
    actual_time_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_tickets')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'profile__role': 'DEV'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.pk} {self.title}"

class TicketRemark(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='remarks')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return f"Remark by {self.author.username} on {self.ticket}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    recipients = models.ManyToManyField(User, related_name='received_messages')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message to {self.recipient.username}: {self.subject}"

class DailyTaskRun(models.Model):
    date = models.DateField(unique=True)
    run_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tasks ran on {self.date}"

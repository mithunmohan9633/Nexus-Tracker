import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bug_tracker.settings')
django.setup()

from django.contrib.auth import get_user_model
from issues.models import Project, Ticket, TicketRemark

User = get_user_model()

Project.objects.all().delete()
Ticket.objects.all().delete()
TicketRemark.objects.all().delete()

users_to_keep = ['admin', 'adithya', 'Nithin', 'nithin', 'Adithya']
users_to_delete = User.objects.exclude(username__in=users_to_keep)
deleted_count = users_to_delete.count()
users_to_delete.delete()

print(f"Deleted {deleted_count} demo users and completely wiped projects and tickets.")

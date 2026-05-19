import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bug_tracker.settings')
django.setup()

from django.contrib.auth import get_user_model
from issues.models import UserProfile, Project

User = get_user_model()

# Create Admin/HR
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')

def create_user(username, role):
    if not User.objects.filter(username=username).exists():
        u = User.objects.create_user(username, f"{username}@test.com", 'password123')
        UserProfile.objects.create(user=u, role=role)
        return u
    return User.objects.get(username=username)

create_user('manager_alice', 'PM')
create_user('apm_bob', 'APM')
create_user('analyst_charlie', 'FA')
create_user('dev_dave', 'DEV')

print("Test users and roles created.")

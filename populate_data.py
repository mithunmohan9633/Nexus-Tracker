import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bug_tracker.settings')
django.setup()

from django.contrib.auth import get_user_model
from issues.models import UserProfile, Project, Ticket, TicketRemark

User = get_user_model()

print('Starting data population...')

def get_or_create_user(username, role):
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': f'{username}@example.com'
    })
    if created:
        user.set_password('password123')
        user.save()
        UserProfile.objects.create(user=user, role=role)
    return user

# Create Users
pms = [get_or_create_user(f'pm_mock_{i}', 'PM') for i in range(1, 4)]
apms = [get_or_create_user(f'apm_mock_{i}', 'APM') for i in range(1, 4)]
fas = [get_or_create_user(f'fa_mock_{i}', 'FA') for i in range(1, 6)]
devs = [get_or_create_user(f'dev_mock_{i}', 'DEV') for i in range(1, 11)]

print('Users created.')

# Create Projects
projects = []
for i in range(1, 6):
    project, created = Project.objects.get_or_create(
        name=f'Nexus Sub-System {i}',
        defaults={
            'description': f'Description for sub-system {i}.',
            'apm': random.choice(apms)
        }
    )
    if created:
        # Assign random FAs and DEVs
        project.functional_analysts.add(*random.sample(fas, k=random.randint(1, 3)))
        project.developers.add(*random.sample(devs, k=random.randint(2, 5)))
    projects.append(project)

print('Projects created.')

# Create Tickets
statuses = ['TODO', 'IN_PROGRESS', 'PENDING_REVIEW', 'DONE']
priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

for p in projects:
    # Get team for this project
    team_fas = list(p.functional_analysts.all())
    team_devs = list(p.developers.all())
    
    if not team_fas or not team_devs:
        continue
        
    for i in range(1, random.randint(6, 12)):
        status = random.choice(statuses)
        reporter = random.choice(team_fas)
        
        # 20% chance of unassigned if not done
        if status == 'TODO' and random.random() < 0.2:
            assignee = None
        else:
            assignee = random.choice(team_devs)
            
        ticket, created = Ticket.objects.get_or_create(
            title=f'Bug {i} in {p.name}',
            project=p,
            defaults={
                'modules': f'Module-{random.randint(1,5)}',
                'current_behaviour': 'System throws error on click.',
                'expected_behaviour': 'System should proceed to next page.',
                'status': status,
                'priority': random.choice(priorities),
                'reporter': reporter,
                'assignee': assignee,
                'issue_identified_date': timezone.now().date() - timedelta(days=random.randint(0, 10))
            }
        )
        
        if created and status in ['PENDING_REVIEW', 'DONE']:
            TicketRemark.objects.create(
                ticket=ticket,
                author=assignee if assignee else reporter,
                text='System auto-generated remark for status update.',
                is_system=True
            )

print('Tickets created successfully! Test environment populated.')

from datetime import timedelta
from django.utils import timezone
from .models import Project, Message, DailyTaskRun
from django.db import IntegrityError

class ReminderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.check_deadlines()
        response = self.get_response(request)
        return response

    def check_deadlines(self):
        try:
            today = timezone.now().date()
            if not DailyTaskRun.objects.filter(date=today).exists():
                DailyTaskRun.objects.create(date=today)
                self.send_reminders(today)
        except Exception:
            pass

    def send_reminders(self, today):
        target_date = today + timedelta(days=7)
        projects = Project.objects.filter(deadline=target_date)
        
        for project in projects:
            recipients = set()
            if project.apm:
                recipients.add(project.apm)
            for fa in project.functional_analysts.all():
                recipients.add(fa)
            for dev in project.developers.all():
                recipients.add(dev)
            
            for recipient in recipients:
                Message.objects.create(
                    recipient=recipient,
                    project=project,
                    subject=f"REMINDER: Project '{project.name}' Deadline in 7 Days!",
                    body=f"This is an automated system reminder.\n\nThe project '{project.name}' is scheduled to hit its deadline on {project.deadline}.\n\nPlease ensure all critical issues are resolved and verified."
                )

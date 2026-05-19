from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile, Project, Ticket, TicketRemark

class BugTrackerTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.pm = User.objects.create_user('pm_user', 'pm@example.com', 'password')
        self.apm = User.objects.create_user('apm_user', 'apm@example.com', 'password')
        self.fa = User.objects.create_user('fa_user', 'fa@example.com', 'password')
        self.dev1 = User.objects.create_user('dev1', 'dev1@example.com', 'password')
        self.dev2 = User.objects.create_user('dev2', 'dev2@example.com', 'password')

        UserProfile.objects.create(user=self.pm, role='PM')
        UserProfile.objects.create(user=self.apm, role='APM')
        UserProfile.objects.create(user=self.fa, role='FA')
        UserProfile.objects.create(user=self.dev1, role='DEV')
        UserProfile.objects.create(user=self.dev2, role='DEV')

        self.project = Project.objects.create(
            name='Test Project',
            description='Testing project',
            apm=self.apm
        )
        self.project.functional_analysts.add(self.fa)
        self.project.developers.add(self.dev1, self.dev2)

        self.ticket = Ticket.objects.create(
            project=self.project,
            title='Test Bug',
            current_behaviour='It breaks',
            expected_behaviour='It works',
            status='TODO',
            priority='MEDIUM',
            reporter=self.fa,
            assignee=self.dev1
        )

    def test_model_string_representations(self):
        self.assertEqual(str(self.pm.profile), 'pm_user - Project Manager')
        self.assertEqual(str(self.project), 'Test Project')
        self.assertTrue('Test Bug' in str(self.ticket))

    def test_ticket_defaults(self):
        ticket = Ticket.objects.create(
            project=self.project,
            title='Another Bug',
            reporter=self.fa
        )
        self.assertEqual(ticket.status, 'TODO')
        self.assertEqual(ticket.priority, 'MEDIUM')
        self.assertIsNone(ticket.assignee)

    def test_dashboard_access_by_role(self):
        self.client.login(username='pm_user', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'dashboard_pm.html')
        
        self.client.login(username='apm_user', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'dashboard_apm.html')

        self.client.login(username='fa_user', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'dashboard_fa.html')

        self.client.login(username='dev1', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'dashboard_dev.html')

        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('hr_dashboard'))

    def test_hr_dashboard_protection(self):
        self.client.login(username='pm_user', password='password')
        response = self.client.get(reverse('hr_dashboard'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_fa_ticket_creation(self):
        self.client.login(username='fa_user', password='password')
        url = reverse('ticket_create') + '?project=' + str(self.project.pk)
        response = self.client.post(url, {
            'title': 'New Integration Bug',
            'current_behaviour': 'Error 500',
            'expected_behaviour': 'Success 200',
            'priority': 'HIGH',
            'assignee': self.dev2.pk
        })
        self.assertRedirects(response, reverse('dashboard'))
        ticket = Ticket.objects.get(title='New Integration Bug')
        self.assertEqual(ticket.reporter, self.fa)
        self.assertEqual(ticket.assignee, self.dev2)

    def test_dev_status_update(self):
        self.client.login(username='dev1', password='password')
        url = reverse('ticket_detail', args=[self.ticket.pk])
        response = self.client.post(url, {
            'update_status': '',
            'status': 'PENDING_REVIEW'
        })
        self.assertRedirects(response, url)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'PENDING_REVIEW')

    def test_fa_ticket_verify_approve(self):
        self.ticket.status = 'PENDING_REVIEW'
        self.ticket.save()
        self.client.login(username='fa_user', password='password')
        url = reverse('ticket_verify', args=[self.ticket.pk])
        response = self.client.post(url, {
            'action': 'approve'
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'DONE')

    def test_fa_ticket_verify_reject(self):
        self.ticket.status = 'PENDING_REVIEW'
        self.ticket.save()
        self.client.login(username='fa_user', password='password')
        url = reverse('ticket_verify', args=[self.ticket.pk])
        response = self.client.post(url, {
            'action': 'reject',
            'rejection_reason': 'Still broken'
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'IN_PROGRESS')

    def test_dev_reassign_ticket(self):
        self.client.login(username='dev1', password='password')
        url = reverse('ticket_reassign', args=[self.ticket.pk])
        response = self.client.post(url, {
            'new_assignee': self.dev2.pk
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assignee, self.dev2)

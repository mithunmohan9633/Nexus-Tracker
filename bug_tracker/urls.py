
from django.http import HttpResponse
from django.core.management import call_command

from django.contrib.auth.models import User
from issues.models import UserProfile
def create_admin(request):
    try:
        user, created = User.objects.get_or_create(username='admin')
        if created:
            user.set_password('admin123')
            user.is_superuser = True
            user.is_staff = True
            user.save()
            UserProfile.objects.get_or_create(user=user, role='HR', full_name='System Admin')
        return HttpResponse('Admin created! You can now login with username: admin, password: admin123')
    except Exception as e:
        return HttpResponse(f'Error: {e}')

def run_migrations(request):
    try:
        call_command('migrate')
        return HttpResponse('Migrations ran successfully!')
    except Exception as e:
        return HttpResponse(f'Error: {e}')

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('create-admin-secret/', create_admin),
    path('run-migrations-secret/', run_migrations),
    path('admin/', admin.site.urls),
    path('', include('issues.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]


from django.http import HttpResponse
from django.core.management import call_command
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
    path('run-migrations-secret/', run_migrations),
    path('admin/', admin.site.urls),
    path('', include('issues.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

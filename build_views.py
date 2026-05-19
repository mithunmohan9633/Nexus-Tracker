import os

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. issues/forms.py
forms_py = '''from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ticket Title'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Detailed description', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
        }
'''
write_file('issues/forms.py', forms_py)

# 2. issues/views.py
views_py = '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Ticket
from .forms import TicketForm

@login_required
def dashboard(request):
    open_tickets = Ticket.objects.exclude(status='DONE')
    my_tickets = open_tickets.filter(assignee=request.user)
    recent_tickets = Ticket.objects.all().order_by('-updated_at')[:5]
    
    context = {
        'total_open': open_tickets.count(),
        'my_tickets_count': my_tickets.count(),
        'recent_tickets': recent_tickets,
    }
    return render(request, 'dashboard.html', context)

@login_required
def ticket_list(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'issues/ticket_list.html', {'tickets': tickets})

@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reporter = request.user
            ticket.save()
            return redirect('dashboard')
    else:
        form = TicketForm()
    return render(request, 'issues/ticket_form.html', {'form': form, 'action': 'Create'})

@login_required
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        # Adding status to update view manually or we can add it to form
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.status = request.POST.get('status', ticket.status)
            ticket.save()
            return redirect('dashboard')
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'issues/ticket_form.html', {'form': form, 'ticket': ticket, 'action': 'Update'})
'''
write_file('issues/views.py', views_py)

# 3. issues/urls.py
urls_py = '''from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/new/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:pk>/edit/', views.ticket_update, name='ticket_update'),
]
'''
write_file('issues/urls.py', urls_py)

# 4. bug_tracker/urls.py
main_urls = '''from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('issues.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
'''
write_file('bug_tracker/urls.py', main_urls)
print("Files generated successfully.")

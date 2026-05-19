import os

forms_path = 'issues/forms.py'
with open(forms_path, 'r', encoding='utf-8') as f:
    forms_content = f.read()

hr_forms = '''
class EmployeeCreationForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['username', 'password', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'})
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user
'''
if 'EmployeeCreationForm' not in forms_content:
    with open(forms_path, 'a', encoding='utf-8') as f:
        f.write(hr_forms)

views_path = 'issues/views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    views_content = f.read()

# Replace the beginning of the dashboard view to catch superuser
old_dash = '''@login_required
def dashboard(request):
    role = get_role(request.user)'''
new_dash = '''@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('hr_dashboard')
    role = get_role(request.user)'''
views_content = views_content.replace(old_dash, new_dash)

if 'def hr_dashboard' not in views_content:
    hr_views = '''
from django.contrib.auth.models import User
from .forms import EmployeeCreationForm

@login_required
def hr_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    employees = UserProfile.objects.all().select_related('user')
    context = {
        'role_title': 'HR / Administration',
        'total_employees': employees.count(),
        'projects_count': Project.objects.count(),
        'employees': employees
    }
    return render(request, 'dashboard_hr.html', context)

@login_required
def employee_create(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hr_dashboard')
    else:
        form = EmployeeCreationForm()
    return render(request, 'issues/generic_form.html', {'form': form, 'title': 'Create New Employee'})
'''
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(views_content + hr_views)

urls_path = 'issues/urls.py'
with open(urls_path, 'r', encoding='utf-8') as f:
    urls_content = f.read()

old_urls = "path('projects/new/', views.project_create, name='project_create'),"
new_urls = '''path('projects/new/', views.project_create, name='project_create'),
    path('hr/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/employees/new/', views.employee_create, name='employee_create'),'''
if 'hr_dashboard' not in urls_content:
    urls_content = urls_content.replace(old_urls, new_urls)
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(urls_content)

# HTML templates
hr_html = '''{% extends 'base.html' %}
{% block content %}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
    <h1>{{ role_title }} Dashboard</h1>
    <a href="{% url 'employee_create' %}" class="btn btn-primary btn-header" style="background: var(--accent-green);">+ Add Employee</a>
</div>

<div class="metrics-grid">
    <div class="metric-card" style="border-color: var(--accent-green);">
        <h3 style="color: var(--accent-green);">Total Active Employees</h3>
        <div class="value">{{ total_employees }}</div>
    </div>
    <div class="metric-card">
        <h3>Total Active Projects</h3>
        <div class="value">{{ projects_count }}</div>
    </div>
</div>

<h2>Company Directory</h2>
<div style="background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; margin-top: 16px;">
    <table>
        <thead>
            <tr>
                <th>Username</th>
                <th>Assigned Role</th>
                <th>System ID</th>
            </tr>
        </thead>
        <tbody>
            {% for emp in employees %}
            <tr>
                <td style="color: var(--text-primary); font-weight: 500;">{{ emp.user.username }}</td>
                <td>{{ emp.get_role_display }}</td>
                <td style="color: var(--text-muted); font-family: monospace;">#{{ emp.user.id }}</td>
            </tr>
            {% empty %}
            <tr><td colspan="3" style="text-align:center; color: var(--text-muted); padding: 40px;">No employees provisioned yet.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
'''
with open('templates/dashboard_hr.html', 'w', encoding='utf-8') as f:
    f.write(hr_html)

print("HR logic built successfully.")

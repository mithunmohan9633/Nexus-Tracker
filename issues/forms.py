from django import forms
from .models import Project, Ticket, TicketRemark, UserProfile, Message
from django.contrib.auth.models import User

class PMProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'apm', 'deadline']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'apm': forms.Select(attrs={'class': 'form-input'}),
            'deadline': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['apm'].queryset = User.objects.filter(profile__role='APM')

class APMTeamForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['functional_analysts', 'developers']
        widgets = {
            'functional_analysts': forms.CheckboxSelectMultiple(),
            'developers': forms.CheckboxSelectMultiple(),
        }

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'modules', 'issue_identified_date', 'path', 'current_behaviour', 'expected_behaviour', 'examples', 'api_or_other_datas', 'priority', 'assignee', 'estimated_time_hours']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'modules': forms.TextInput(attrs={'class': 'form-input'}),
            'issue_identified_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'path': forms.TextInput(attrs={'class': 'form-input'}),
            'current_behaviour': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'expected_behaviour': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'examples': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'api_or_other_datas': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'assignee': forms.Select(attrs={'class': 'form-input'}),
            'estimated_time_hours': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
        }
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assignee'].queryset = project.developers.all()
        else:
            self.fields['assignee'].queryset = User.objects.filter(profile__role='DEV')

class RemarkForm(forms.ModelForm):
    class Meta:
        model = TicketRemark
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Add a remark...'}),
        }

class StatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
        }

class EmployeeCreationForm(forms.ModelForm):
    full_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter Full Name'}))
    mobile_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter Mobile Number'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Enter Password'}))
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))
    
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'mobile_number', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter Email'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another one.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                full_name=self.cleaned_data['full_name'],
                mobile_number=self.cleaned_data['mobile_number']
            )
        return user

class ComposeMessageForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-input'}))
    body = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 5}))
    project = forms.ModelChoiceField(queryset=Project.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-input'}))

    def __init__(self, *args, **kwargs):
        exclude_user = kwargs.pop('exclude_user', None)
        super().__init__(*args, **kwargs)
        if exclude_user:
            self.fields['recipients'].queryset = User.objects.exclude(pk=exclude_user.pk)

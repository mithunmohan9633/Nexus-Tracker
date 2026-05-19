from django.contrib import admin
from .models import UserProfile, Project, Ticket, TicketRemark

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'apm', 'created_at')
    filter_horizontal = ('functional_analysts', 'developers')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'assignee', 'reporter')
    list_filter = ('status', 'priority', 'project')

admin.site.register(TicketRemark)

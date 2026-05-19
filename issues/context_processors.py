from .models import Message
def unread_messages(request):
    if request.user.is_authenticated:
        return {'unread_messages_count': Message.objects.filter(recipients=request.user, is_read=False).count()}
    return {}

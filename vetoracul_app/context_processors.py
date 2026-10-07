from django.utils import timezone

from .models import Reminder, VetAccessRequest


def notifications(request):
    """
    Контекст-процессор: уведомления для шапки сайта.
    Доступен во всех шаблонах (там, где рендерится base_app.html).
    """
    empty = {
        'pending_vet_requests': [],
        'past_pending_reminders': [],
        'notifications_count': 0,
    }

    if not request.user.is_authenticated:
        return empty

    # Уведомления этого типа — только для владельцев питомцев.
    # Для ветеринаров (и админов без питомцев) оставляем пустыми.
    if request.user.role != 'user':
        return empty

    user = request.user
    pets = (user.pets.all() | user.co_owned_pets.all()).distinct()

    pending_vet_requests = (
        VetAccessRequest.objects
        .filter(pet__owner=user, status=VetAccessRequest.Status.PENDING)
        .select_related('vet', 'pet')
        .order_by('-created_at')
    )

    past_pending_reminders = (
        Reminder.objects
        .filter(
            pet__in=pets,
            status=Reminder.Status.PENDING,
            date__lt=timezone.now().date(),
        )
        .select_related('pet')
        .order_by('-date')[:20]
    )

    return {
        'pending_vet_requests': pending_vet_requests,
        'past_pending_reminders': past_pending_reminders,
        'notifications_count': pending_vet_requests.count() + past_pending_reminders.count(),
    }
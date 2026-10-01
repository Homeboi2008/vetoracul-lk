from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Pet


@receiver(pre_save, sender=Pet)
def pet_health_status_changed(sender, instance, **kwargs):
    """Отправляет письмо владельцу и совладельцам, если состояние стало 'critical'."""
    if not instance.pk:
        return  # новая карточка, пропускаем

    try:
        old = Pet.objects.get(pk=instance.pk)
    except Pet.DoesNotExist:
        return

    # Изменение на critical и раньше был другой статус
    if old.health_status != instance.health_status and instance.health_status == Pet.HealthStatus.CRITICAL:
        owner = instance.owner
        if not owner.notify_urgent:
            return

        recipients = []
        if owner.email:
            recipients.append(owner.email)
        for co in instance.co_owners.all():
            if co.email:
                recipients.append(co.email)

        if not recipients:
            return

        subject = f'⚠️ Критическое состояние: {instance.name}'
        message = (
            f'Здравствуйте!\n\n'
            f'Состояние здоровья питомца {instance.name} изменилось на '
            f'«Критическое состояние».\n\n'
            f'Пожалуйста, свяжитесь с ветеринаром как можно скорее.\n\n'
            f'— ВетОракул'
        )

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Ошибка отправки urgent-уведомления: %s', e)
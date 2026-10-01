from django.core.management.base import BaseCommand
from vetoracul_app.views import _send_pending_reminder_notifications


class Command(BaseCommand):
    help = 'Отправляет email-уведомления о напоминаниях на завтра'

    def handle(self, *args, **options):
        sent = _send_pending_reminder_notifications()
        self.stdout.write(self.style.SUCCESS(f'Отправлено уведомлений: {sent}'))
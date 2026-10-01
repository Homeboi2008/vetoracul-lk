from django.apps import AppConfig


class VetoraculAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vetoracul_app'

    def ready(self):
        import vetoracul_app.signals
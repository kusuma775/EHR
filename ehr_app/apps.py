from django.apps import AppConfig


class EhrAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ehr_app'
    def ready(self):
        import ehr_app.signals

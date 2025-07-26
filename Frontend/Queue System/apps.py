from django.apps import AppConfig

class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Frontend'

    # def ready(self):
    #     from threading import Thread
    #     from .scheduler import scheduler_loop
    #     Thread(target=scheduler_loop, daemon=True).start()
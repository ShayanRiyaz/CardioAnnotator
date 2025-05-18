from django.apps import AppConfig

class AnnotationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'annotation'    # ← this must match your app folder

    def ready(self):
        # import your Dash app so it gets registered on startup
        import annotation.dashboards.annotation.app
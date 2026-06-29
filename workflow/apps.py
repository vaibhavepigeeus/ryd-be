from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "workflow"

    def ready(self):
        import os
        if os.environ.get("RUN_MAIN") == "true":
            from .scheduler import run
            run()

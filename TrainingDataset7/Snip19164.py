def db_for_write(self, model, **hints):
        if model._meta.app_label == "django_cache":
            return "other"
        return None
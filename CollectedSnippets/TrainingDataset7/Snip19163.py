def db_for_read(self, model, **hints):
        if model._meta.app_label == "django_cache":
            return "other"
        return None
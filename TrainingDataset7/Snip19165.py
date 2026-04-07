def allow_migrate(self, db, app_label, **hints):
        if app_label == "django_cache":
            return db == "other"
        return None
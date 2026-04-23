def db_for_write(self, model, **hints):
        if model._meta.app_label in {"auth", "sessions", "contenttypes"}:
            return "default"
        return "other"
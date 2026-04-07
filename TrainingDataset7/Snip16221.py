def db_for_read(self, model, instance=None, **hints):
        if model._meta.app_label in {"auth", "sessions", "contenttypes"}:
            return "default"
        return "other"
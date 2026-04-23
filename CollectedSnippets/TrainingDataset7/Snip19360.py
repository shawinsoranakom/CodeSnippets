def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == ("other" if model_name.startswith("other") else "default")
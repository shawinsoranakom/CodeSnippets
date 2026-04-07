def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "other":
            return model_name == "pet"
        else:
            return model_name != "pet"
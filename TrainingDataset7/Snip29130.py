def db_for_write(self, model, **hints):
        "Point all operations on auth models to 'other'"
        if model._meta.app_label == "auth":
            return "other"
        return None
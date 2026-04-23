def allow_migrate(self, db, app_label, **hints):
        "Make sure the auth app only appears on the 'other' db"
        if app_label == "auth":
            return db == "other"
        return None
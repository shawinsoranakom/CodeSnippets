def allow_migrate(self, db, app_label, **hints):
        return hints.get("a_hint", False)
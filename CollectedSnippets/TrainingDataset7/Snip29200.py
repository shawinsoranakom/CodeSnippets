def allow_migrate(self, db, app_label, **hints):
        return db == DEFAULT_DB_ALIAS
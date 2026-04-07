def create_connection(self, alias):
        db = self.settings[alias]
        backend = load_backend(db["ENGINE"])
        return backend.DatabaseWrapper(db, alias)
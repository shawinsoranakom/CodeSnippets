def __enter__(self):
        self.deferred_sql = []
        if self.atomic_migration:
            self.atomic = atomic(self.connection.alias)
            self.atomic.__enter__()
        return self
def __iter__(self):
        with self.db.wrap_database_errors:
            yield from self.cursor
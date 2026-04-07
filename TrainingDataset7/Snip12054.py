def db(self):
        """Return the database used if this query is executed now."""
        return self._db or router.db_for_read(self.model, **self._hints)
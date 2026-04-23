def effective_default(self, field):
        """Return a field's effective database default value."""
        return field.get_db_prep_save(self._effective_default(field), self.connection)
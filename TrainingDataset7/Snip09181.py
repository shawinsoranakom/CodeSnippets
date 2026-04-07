def _savepoint_allowed(self):
        # Savepoints cannot be created outside a transaction
        return self.features.uses_savepoints and not self.get_autocommit()
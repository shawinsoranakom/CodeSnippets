def flush(self):
        """Delete all migration records. Useful for testing migrations."""
        self.migration_qs.all().delete()
def has_changed(self):
        """Return True if data differs from initial."""
        return bool(self.changed_data)
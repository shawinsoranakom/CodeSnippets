def has_changed(self):
        """Return True if data in any form differs from initial."""
        return any(form.has_changed() for form in self)
def errors(self):
        """Return an ErrorDict for the data provided for the form."""
        if self._errors is None:
            self.full_clean()
        return self._errors
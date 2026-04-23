def initial_forms(self):
        """Return a list of all the initial forms in this formset."""
        return self.forms[: self.initial_form_count()]
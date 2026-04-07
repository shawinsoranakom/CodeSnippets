def is_valid(self):
        """Return True if every form in self.forms is valid."""
        if not self.is_bound:
            return False
        # Accessing errors triggers a full clean the first time only.
        self.errors
        # List comprehension ensures is_valid() is called for all forms.
        # Forms due to be deleted shouldn't cause the formset to be invalid.
        forms_valid = all(
            [
                form.is_valid()
                for form in self.forms
                if not (self.can_delete and self._should_delete_form(form))
            ]
        )
        return forms_valid and not self.non_form_errors()
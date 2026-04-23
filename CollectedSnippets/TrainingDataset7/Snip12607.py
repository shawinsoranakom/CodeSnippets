def total_error_count(self):
        """Return the number of errors across all forms in the formset."""
        return len(self.non_form_errors()) + sum(
            len(form_errors) for form_errors in self.errors
        )
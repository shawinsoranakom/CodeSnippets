def _should_delete_form(self, form):
        """Return whether or not the form was marked for deletion."""
        return form.cleaned_data.get(DELETION_FIELD_NAME, False)
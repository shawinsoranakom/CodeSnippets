def save_existing(self, form, obj, commit=True):
        """Save and return an existing model instance for the given form."""
        return form.save(commit=commit)
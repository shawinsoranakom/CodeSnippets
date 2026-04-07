def save_new(self, form, commit=True):
        """Save and return a new model instance for the given form."""
        return form.save(commit=commit)
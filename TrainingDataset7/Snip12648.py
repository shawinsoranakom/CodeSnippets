def delete_existing(self, obj, commit=True):
        """Deletes an existing model instance."""
        if commit:
            obj.delete()
def deleted_forms(self):
        """Return a list of forms that have been marked for deletion."""
        if not self.is_valid() or not self.can_delete:
            return []
        # construct _deleted_form_indexes which is just a list of form indexes
        # that have had their deletion widget set to True
        if not hasattr(self, "_deleted_form_indexes"):
            self._deleted_form_indexes = []
            for i, form in enumerate(self.forms):
                # If this is an extra form and hasn't changed, ignore it.
                if i >= self.initial_form_count() and not form.has_changed():
                    continue
                if self._should_delete_form(form):
                    self._deleted_form_indexes.append(i)
        return [self.forms[i] for i in self._deleted_form_indexes]
def ordered_forms(self):
        """
        Return a list of form in the order specified by the incoming data.
        Raise an AttributeError if ordering is not allowed.
        """
        if not self.is_valid() or not self.can_order:
            raise AttributeError(
                "'%s' object has no attribute 'ordered_forms'" % self.__class__.__name__
            )
        # Construct _ordering, which is a list of (form_index,
        # order_field_value) tuples. After constructing this list, we'll sort
        # it by order_field_value so we have a way to get to the form indexes
        # in the order specified by the form data.
        if not hasattr(self, "_ordering"):
            self._ordering = []
            for i, form in enumerate(self.forms):
                # If this is an extra form and hasn't changed, ignore it.
                if i >= self.initial_form_count() and not form.has_changed():
                    continue
                # don't add data marked for deletion to self.ordered_data
                if self.can_delete and self._should_delete_form(form):
                    continue
                self._ordering.append((i, form.cleaned_data[ORDERING_FIELD_NAME]))
            # After we're done populating self._ordering, sort it.
            # A sort function to order things numerically ascending, but
            # None should be sorted below anything else. Allowing None as
            # a comparison value makes it so we can leave ordering fields
            # blank.

            def compare_ordering_key(k):
                if k[1] is None:
                    return (1, 0)  # +infinity, larger than any number
                return (0, k[1])

            self._ordering.sort(key=compare_ordering_key)
        # Return a list of form.cleaned_data dicts in the order specified by
        # the form data.
        return [self.forms[i[0]] for i in self._ordering]
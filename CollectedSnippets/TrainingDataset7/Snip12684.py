def _get_choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, "_choices"):
            return self._choices

        # Otherwise, execute the QuerySet in self.queryset to determine the
        # choices dynamically. Return a fresh ModelChoiceIterator that has not
        # been consumed. Note that we're instantiating a new
        # ModelChoiceIterator *each* time _get_choices() is called (and, thus,
        # each time self.choices is accessed) so that we can ensure the
        # QuerySet has not been consumed. This construct might look complicated
        # but it allows for lazy evaluation of the queryset.
        return self.iterator(self)
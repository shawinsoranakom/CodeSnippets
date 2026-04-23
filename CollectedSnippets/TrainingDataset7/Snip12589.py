def __repr__(self):
        if self._errors is None:
            is_valid = "Unknown"
        else:
            is_valid = (
                self.is_bound
                and not self._non_form_errors
                and not any(form_errors for form_errors in self._errors)
            )
        return "<%s: bound=%s valid=%s total_forms=%s>" % (
            self.__class__.__qualname__,
            self.is_bound,
            is_valid,
            self.total_form_count(),
        )
def non_field_errors(self):
        """
        Return an ErrorList of errors that aren't associated with a particular
        field -- i.e., from Form.clean(). Return an empty ErrorList if there
        are none.
        """
        return self.errors.get(
            NON_FIELD_ERRORS,
            self.error_class(error_class="nonfield", renderer=self.renderer),
        )
def get_limit_choices_to(self):
        """
        Return ``limit_choices_to`` for this form field.

        If it is a callable, invoke it and return the result.
        """
        if callable(self.limit_choices_to):
            return self.limit_choices_to()
        return self.limit_choices_to
def get_limit_choices_to(self):
        """
        Return ``limit_choices_to`` for this model field.

        If it is a callable, it will be invoked and the result will be
        returned.
        """
        if callable(self.remote_field.limit_choices_to):
            return self.remote_field.limit_choices_to()
        return self.remote_field.limit_choices_to
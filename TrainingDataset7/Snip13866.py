def settings(self, **kwargs):
        """
        A context manager that temporarily sets a setting and reverts to the
        original value when exiting the context.
        """
        return override_settings(**kwargs)
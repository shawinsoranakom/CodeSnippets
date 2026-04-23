def modify_settings(self, **kwargs):
        """
        A context manager that temporarily applies changes to a list setting
        and reverts back to the original value when exiting the context.
        """
        return modify_settings(**kwargs)
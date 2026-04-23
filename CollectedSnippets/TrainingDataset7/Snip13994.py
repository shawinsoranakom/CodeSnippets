def save_options(self, test_func):
        if test_func._overridden_settings is None:
            test_func._overridden_settings = self.options
        else:
            # Duplicate dict to prevent subclasses from altering their parent.
            test_func._overridden_settings = {
                **test_func._overridden_settings,
                **self.options,
            }
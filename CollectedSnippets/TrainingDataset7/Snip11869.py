def verbose_name_raw(self):
        """Return the untranslated verbose name."""
        if isinstance(self.verbose_name, str):
            return self.verbose_name
        with override(None):
            return str(self.verbose_name)
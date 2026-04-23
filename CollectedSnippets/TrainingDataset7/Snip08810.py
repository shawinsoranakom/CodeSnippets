def settings_available(self):
        try:
            settings.LOCALE_PATHS
        except ImproperlyConfigured:
            if self.verbosity > 1:
                self.stderr.write("Running without configured settings.")
            return False
        return True
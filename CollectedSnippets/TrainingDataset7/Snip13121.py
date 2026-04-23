def app_dirname(self):
        raise ImproperlyConfigured(
            "{} doesn't support loading templates from installed "
            "applications.".format(self.__class__.__name__)
        )
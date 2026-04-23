def path(self, name):
        if not self.location:
            raise ImproperlyConfigured(
                "You're using the staticfiles app "
                "without having set the STATIC_ROOT "
                "setting to a filesystem path."
            )
        return super().path(name)
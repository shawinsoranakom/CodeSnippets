def check_apps_ready(self):
        """Raise an exception if all apps haven't been imported yet."""
        if not self.apps_ready:
            from django.conf import settings

            # If "not ready" is due to unconfigured settings, accessing
            # INSTALLED_APPS raises a more helpful ImproperlyConfigured
            # exception.
            settings.INSTALLED_APPS
            raise AppRegistryNotReady("Apps aren't loaded yet.")
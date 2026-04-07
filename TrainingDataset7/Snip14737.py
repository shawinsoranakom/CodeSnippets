def _add_installed_apps_translations(self):
        """Merge translations from each installed app."""
        try:
            app_configs = reversed(apps.get_app_configs())
        except AppRegistryNotReady:
            raise AppRegistryNotReady(
                "The translation infrastructure cannot be initialized before the "
                "apps registry is ready. Check that you don't make non-lazy "
                "gettext calls at import time."
            )
        for app_config in app_configs:
            localedir = os.path.join(app_config.path, "locale")
            if os.path.exists(localedir):
                translation = self._new_gnu_trans(localedir)
                self.merge(translation)
def test_get_containing_app_config_apps_not_ready(self):
        """
        apps.get_containing_app_config() should raise an exception if
        apps.apps_ready isn't True.
        """
        apps.apps_ready = False
        try:
            with self.assertRaisesMessage(
                AppRegistryNotReady, "Apps aren't loaded yet"
            ):
                apps.get_containing_app_config("foo")
        finally:
            apps.apps_ready = True
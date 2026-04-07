def test_get_app_configs(self):
        """
        Tests apps.get_app_configs().
        """
        app_configs = apps.get_app_configs()
        self.assertEqual(
            [app_config.name for app_config in app_configs], SOME_INSTALLED_APPS_NAMES
        )
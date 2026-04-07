def test_installed_apps(self):
        self.assertEqual(
            [app_config.label for app_config in self.class_apps.get_app_configs()],
            ["test_utils"],
        )
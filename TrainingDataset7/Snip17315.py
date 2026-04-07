def test_default_auto_field_setting(self):
        apps_config = apps.get_app_config("apps")
        self.assertEqual(
            apps_config.default_auto_field,
            "django.db.models.SmallAutoField",
        )
        self.assertIs(apps_config._is_default_auto_field_overridden, False)
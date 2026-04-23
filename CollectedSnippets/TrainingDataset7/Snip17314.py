def test_app_default_auto_field(self):
        apps_config = apps.get_app_config("apps")
        self.assertEqual(
            apps_config.default_auto_field,
            "django.db.models.BigAutoField",
        )
        self.assertIs(apps_config._is_default_auto_field_overridden, True)
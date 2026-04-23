def test_foreign_key_swapped(self):
        with isolate_lru_cache(apps.get_swappable_settings_name):
            # It doesn't matter that we swapped out user for permission;
            # there's no validation. We just want to check the setting stuff
            # works.
            field = models.ForeignKey("auth.Permission", models.CASCADE)
            name, path, args, kwargs = field.deconstruct()

        self.assertEqual(path, "django.db.models.ForeignKey")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.permission", "on_delete": models.CASCADE})
        self.assertEqual(kwargs["to"].setting_name, "AUTH_USER_MODEL")

        # Model names are case-insensitive.
        with isolate_lru_cache(apps.get_swappable_settings_name):
            # It doesn't matter that we swapped out user for permission;
            # there's no validation. We just want to check the setting stuff
            # works.
            field = models.ForeignKey("auth.permission", models.CASCADE)
            name, path, args, kwargs = field.deconstruct()

        self.assertEqual(path, "django.db.models.ForeignKey")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.permission", "on_delete": models.CASCADE})
        self.assertEqual(kwargs["to"].setting_name, "AUTH_USER_MODEL")
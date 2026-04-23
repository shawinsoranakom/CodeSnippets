def test_clear_cache(self):
        # Set cache.
        self.assertIsNone(apps.get_swappable_settings_name("admin.LogEntry"))
        apps.get_models()

        apps.clear_cache()

        self.assertEqual(apps.get_swappable_settings_name.cache_info().currsize, 0)
        self.assertEqual(apps.get_models.cache_info().currsize, 0)
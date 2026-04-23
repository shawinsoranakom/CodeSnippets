def test_override_settings_delete(self):
        """
        Allow deletion of a setting in an overridden settings set (#18824)
        """
        previous_i18n = settings.USE_I18N
        previous_tz = settings.USE_TZ
        with self.settings(USE_I18N=False):
            del settings.USE_I18N
            with self.assertRaises(AttributeError):
                getattr(settings, "USE_I18N")
            # Should also work for a non-overridden setting
            del settings.USE_TZ
            with self.assertRaises(AttributeError):
                getattr(settings, "USE_TZ")
            self.assertNotIn("USE_I18N", dir(settings))
            self.assertNotIn("USE_TZ", dir(settings))
        self.assertEqual(settings.USE_I18N, previous_i18n)
        self.assertEqual(settings.USE_TZ, previous_tz)
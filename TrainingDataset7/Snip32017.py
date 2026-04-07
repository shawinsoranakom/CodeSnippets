def test_override_settings_inheritance(self):
        self.assertEqual(settings.ITEMS, ["father", "mother", "child"])
        self.assertEqual(settings.TEST, "override-child")
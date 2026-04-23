def test_setting_non_label(self):
        with override_settings(MODEL_META_TESTS_SWAPPED="not-a-label"):
            self.assertEqual(Swappable._meta.swapped, "not-a-label")
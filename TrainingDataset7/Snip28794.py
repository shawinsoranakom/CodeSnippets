def test_setting_none(self):
        with override_settings(MODEL_META_TESTS_SWAPPED=None):
            self.assertIsNone(Swappable._meta.swapped)
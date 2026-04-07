def test_setting_self(self):
        with override_settings(MODEL_META_TESTS_SWAPPED="model_meta.swappable"):
            self.assertIsNone(Swappable._meta.swapped)
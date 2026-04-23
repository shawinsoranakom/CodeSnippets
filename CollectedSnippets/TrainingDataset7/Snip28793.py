def test_set_and_unset(self):
        with override_settings(MODEL_META_TESTS_SWAPPED="model_meta.Relation"):
            self.assertEqual(Swappable._meta.swapped, "model_meta.Relation")
        self.assertIsNone(Swappable._meta.swapped)
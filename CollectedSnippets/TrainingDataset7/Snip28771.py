def test_label_lower(self):
        for model, expected_result in TEST_RESULTS["lower_labels"].items():
            self.assertEqual(model._meta.label_lower, expected_result)
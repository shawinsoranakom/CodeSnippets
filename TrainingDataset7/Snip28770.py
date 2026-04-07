def test_label(self):
        for model, expected_result in TEST_RESULTS["labels"].items():
            self.assertEqual(model._meta.label, expected_result)
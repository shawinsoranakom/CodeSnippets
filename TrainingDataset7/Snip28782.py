def test_private_fields(self):
        for model, expected_names in TEST_RESULTS["private_fields"].items():
            objects = model._meta.private_fields
            self.assertEqual(sorted(f.name for f in objects), sorted(expected_names))
def test_fields(self):
        for model, expected_result in TEST_RESULTS["fields"].items():
            fields = model._meta.fields
            self.assertEqual([f.attname for f in fields], expected_result)
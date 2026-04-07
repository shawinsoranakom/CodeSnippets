def test_local_concrete_fields(self):
        for model, expected_result in TEST_RESULTS["local_concrete_fields"].items():
            fields = model._meta.local_concrete_fields
            self.assertEqual([f.attname for f in fields], expected_result)
            for f in fields:
                self.assertIsNotNone(f.column)
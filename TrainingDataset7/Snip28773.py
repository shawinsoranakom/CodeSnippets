def test_local_fields(self):
        def is_data_field(f):
            return isinstance(f, Field) and not f.many_to_many

        for model, expected_result in TEST_RESULTS["local_fields"].items():
            fields = model._meta.local_fields
            self.assertEqual([f.attname for f in fields], expected_result)
            for f in fields:
                self.assertEqual(f.model, model)
                self.assertTrue(is_data_field(f))
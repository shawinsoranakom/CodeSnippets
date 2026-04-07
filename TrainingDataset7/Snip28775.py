def test_many_to_many(self):
        for model, expected_result in TEST_RESULTS["many_to_many"].items():
            fields = model._meta.many_to_many
            self.assertEqual([f.attname for f in fields], expected_result)
            for f in fields:
                self.assertTrue(f.many_to_many and f.is_relation)
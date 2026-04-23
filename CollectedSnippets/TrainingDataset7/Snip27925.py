def test_nullable(self):
        m1 = self.nullable_model.objects.create()
        none_val = "" if connection.features.interprets_empty_strings_as_nulls else None
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m1.lower_name, none_val)
        m2 = self.nullable_model.objects.create(name="NaMe")
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m2.lower_name, "name")
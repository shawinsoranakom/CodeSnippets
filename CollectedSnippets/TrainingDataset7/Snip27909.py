def test_full_clean(self):
        m = self.base_model(a=1, b=2)
        # full_clean() ignores GeneratedFields.
        m.full_clean()
        m.save()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 3)
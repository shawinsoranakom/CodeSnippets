def test_create(self):
        m = self.base_model.objects.create(a=1, b=2)
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 3)
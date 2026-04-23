def test_save_model_with_pk(self):
        m = self.base_model(pk=1, a=1, b=2)
        m.save()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 3)
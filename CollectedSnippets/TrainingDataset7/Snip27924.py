def test_model_with_params(self):
        m = self.params_model.objects.create()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, "Constant")
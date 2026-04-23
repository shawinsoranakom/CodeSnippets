def test_case_when_db_default_returning(self):
        m = DBDefaultsFunction.objects.create()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.case_when, 3)
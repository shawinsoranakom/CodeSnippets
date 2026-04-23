def test_db_default_function(self):
        m = DBDefaultsFunction.objects.create()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 4
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertAlmostEqual(m.number, pi)
            self.assertEqual(m.year, datetime.now(UTC).year)
            self.assertAlmostEqual(m.added, pi + 4.5)
            self.assertEqual(m.multiple_subfunctions, 4.5)
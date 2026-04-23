def test_null_db_default(self):
        obj1 = DBDefaults.objects.create()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(obj1.null, 1.1)

        obj2 = DBDefaults.objects.create(null=None)
        with self.assertNumQueries(0):
            self.assertIsNone(obj2.null)
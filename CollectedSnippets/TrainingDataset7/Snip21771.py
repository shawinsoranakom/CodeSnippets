def test_field_db_defaults_returning(self):
        a = DBArticle()
        a.save()
        self.assertIsInstance(a.id, int)
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 3
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(a.headline, "Default headline")
            self.assertIsInstance(a.pub_date, datetime)
            self.assertEqual(a.cost, Decimal("3.33"))
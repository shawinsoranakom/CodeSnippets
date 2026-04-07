def test_get_constraints_indexes_orders(self):
        """
        Indexes have the 'orders' key with a list of 'ASC'/'DESC' values.
        """
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, Article._meta.db_table
            )
        indexes_verified = 0
        expected_columns = [
            ["headline", "pub_date"],
            ["headline", "response_to_id", "pub_date", "reporter_id"],
        ]
        if connection.features.indexes_foreign_keys:
            expected_columns += [
                ["reporter_id"],
                ["response_to_id"],
            ]
        for val in constraints.values():
            if val["index"] and not (val["primary_key"] or val["unique"]):
                self.assertIn(val["columns"], expected_columns)
                self.assertEqual(val["orders"], ["ASC"] * len(val["columns"]))
                indexes_verified += 1
        self.assertEqual(indexes_verified, len(expected_columns))
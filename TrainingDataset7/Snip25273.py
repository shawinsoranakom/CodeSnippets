def test_get_table_description_col_lengths(self):
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(
                cursor, Reporter._meta.db_table
            )
        self.assertEqual(
            [
                r[2]
                for r in desc
                if connection.introspection.get_field_type(r[1], r) == "CharField"
            ],
            [30, 30, 254],
        )
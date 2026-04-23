def test_get_table_description_names(self):
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(
                cursor, Reporter._meta.db_table
            )
        self.assertEqual(
            [r[0] for r in desc], [f.column for f in Reporter._meta.fields]
        )
def test_bigautofield(self):
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(
                cursor, City._meta.db_table
            )
        self.assertIn(
            connection.features.introspected_field_types["BigAutoField"],
            [connection.introspection.get_field_type(r[1], r) for r in desc],
        )
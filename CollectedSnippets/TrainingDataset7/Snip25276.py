def test_smallautofield(self):
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(
                cursor, Country._meta.db_table
            )
        self.assertIn(
            connection.features.introspected_field_types["SmallAutoField"],
            [connection.introspection.get_field_type(r[1], r) for r in desc],
        )
def test_get_table_description_types(self):
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(
                cursor, Reporter._meta.db_table
            )
        self.assertEqual(
            [connection.introspection.get_field_type(r[1], r) for r in desc],
            [
                connection.features.introspected_field_types[field]
                for field in (
                    "BigAutoField",
                    "CharField",
                    "CharField",
                    "CharField",
                    "BigIntegerField",
                    "BinaryField",
                    "SmallIntegerField",
                    "DurationField",
                )
            ],
        )
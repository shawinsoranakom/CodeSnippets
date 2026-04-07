def test_bulk_batch_size_respects_variable_limit(self):
        first_name_field = Person._meta.get_field("first_name")
        last_name_field = Person._meta.get_field("last_name")
        limit_name = sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER
        current_limit = connection.features.max_query_params
        self.assertEqual(
            connection.ops.bulk_batch_size(
                [first_name_field, last_name_field], [Person()]
            ),
            current_limit // 2,
        )
        new_limit = min(42, current_limit)
        try:
            connection.connection.setlimit(limit_name, new_limit)
            self.assertEqual(
                connection.ops.bulk_batch_size(
                    [first_name_field, last_name_field], [Person()]
                ),
                new_limit // 2,
            )
        finally:
            connection.connection.setlimit(limit_name, current_limit)
        self.assertEqual(
            connection.ops.bulk_batch_size(
                [first_name_field, last_name_field], [Person()]
            ),
            current_limit // 2,
        )
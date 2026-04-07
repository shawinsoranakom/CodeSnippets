def test_insert_returning(self):
        with CaptureQueriesContext(connection) as captured_queries:
            DumbCategory.objects.create()
        self.assertIn(
            "RETURNING %s.%s"
            % (
                connection.ops.quote_name(DumbCategory._meta.db_table),
                connection.ops.quote_name(DumbCategory._meta.get_field("id").column),
            ),
            captured_queries[-1]["sql"],
        )
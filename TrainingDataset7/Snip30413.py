def test_insert_returning_multiple(self):
        with CaptureQueriesContext(connection) as captured_queries:
            obj = ReturningModel.objects.create()
        table_name = connection.ops.quote_name(ReturningModel._meta.db_table)
        self.assertIn(
            "RETURNING %s.%s, %s.%s"
            % (
                table_name,
                connection.ops.quote_name(ReturningModel._meta.get_field("id").column),
                table_name,
                connection.ops.quote_name(
                    ReturningModel._meta.get_field("created").column
                ),
            ),
            captured_queries[-1]["sql"],
        )
        self.assertEqual(
            captured_queries[-1]["sql"]
            .split("RETURNING ")[1]
            .count(
                connection.ops.quote_name(
                    ReturningModel._meta.get_field("created").column
                ),
            ),
            1,
        )
        self.assertTrue(obj.pk)
        self.assertIsInstance(obj.created, datetime.datetime)
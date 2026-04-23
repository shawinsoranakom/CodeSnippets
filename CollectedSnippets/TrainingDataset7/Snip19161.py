def test_createcachetable_with_table_argument(self):
        """
        Delete and recreate cache table with legacy behavior (explicitly
        specifying the table name).
        """
        self.drop_table()
        out = io.StringIO()
        management.call_command(
            "createcachetable",
            "test cache table",
            verbosity=2,
            stdout=out,
        )
        self.assertEqual(out.getvalue(), "Cache table 'test cache table' created.\n")
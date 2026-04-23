def test_introspection_errors(self):
        """
        Introspection errors should not crash the command, and the error should
        be visible in the output.
        """
        out = StringIO()
        with mock.patch(
            "django.db.connection.introspection.get_table_list",
            return_value=[TableInfo(name="nonexistent", type="t")],
        ):
            call_command("inspectdb", stdout=out)
        output = out.getvalue()
        self.assertIn("# Unable to inspect table 'nonexistent'", output)
        # The error message depends on the backend
        self.assertIn("# The error was:", output)
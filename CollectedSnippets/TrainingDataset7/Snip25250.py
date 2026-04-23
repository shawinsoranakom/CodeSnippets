def test_unsupported_unique_together(self):
        """Unsupported index types (COALESCE here) are skipped."""
        cursor_execute(
            "CREATE UNIQUE INDEX Findex ON %s "
            "(id, people_unique_id, COALESCE(message_id, -1))"
            % PeopleMoreData._meta.db_table
        )
        self.addCleanup(cursor_execute, "DROP INDEX Findex")
        out = StringIO()
        call_command(
            "inspectdb",
            table_name_filter=lambda tn: tn.startswith(PeopleMoreData._meta.db_table),
            stdout=out,
        )
        output = out.getvalue()
        self.assertIn("# A unique constraint could not be introspected.", output)
        self.assertEqual(self.unique_re.findall(output), ["('id', 'people_unique')"])
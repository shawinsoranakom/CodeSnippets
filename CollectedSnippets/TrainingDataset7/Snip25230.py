def test_table_option(self):
        """
        inspectdb can inspect a subset of tables by passing the table names as
        arguments.
        """
        out = StringIO()
        call_command("inspectdb", "inspectdb_people", stdout=out)
        output = out.getvalue()
        self.assertIn("class InspectdbPeople(models.Model):", output)
        self.assertNotIn("InspectdbPeopledata", output)
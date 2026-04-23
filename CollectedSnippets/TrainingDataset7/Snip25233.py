def test_json_field(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_jsonfieldcolumntype", stdout=out)
        output = out.getvalue()
        if not connection.features.interprets_empty_strings_as_nulls:
            self.assertIn("json_field = models.JSONField()", output)
        self.assertIn(
            "null_json_field = models.JSONField(blank=True, null=True)", output
        )
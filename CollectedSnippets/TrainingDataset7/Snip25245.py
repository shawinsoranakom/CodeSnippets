def test_table_name_introspection(self):
        """
        Introspection of table names containing special characters,
        unsuitable for Python identifiers
        """
        out = StringIO()
        call_command("inspectdb", table_name_filter=special_table_only, stdout=out)
        output = out.getvalue()
        self.assertIn("class InspectdbSpecialTableName(models.Model):", output)
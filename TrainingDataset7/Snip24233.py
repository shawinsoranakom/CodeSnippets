def test_using_sql(self):
        if not connection.ops.postgis:
            self.skipTest("This is a PostGIS-specific test.")
        index = Index(fields=["point"])
        editor = connection.schema_editor()
        self.assertIn(
            "%s USING " % editor.quote_name(City._meta.db_table),
            str(index.create_sql(City, editor)),
        )
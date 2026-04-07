def test_composite_primary_key(self):
        out = StringIO()
        field_type = connection.features.introspected_field_types["IntegerField"]
        call_command("inspectdb", "inspectdb_compositepkmodel", stdout=out)
        output = out.getvalue()
        self.assertIn(
            "pk = models.CompositePrimaryKey('column_1', 'column_2')",
            output,
        )
        self.assertIn(f"column_1 = models.{field_type}()", output)
        self.assertIn(f"column_2 = models.{field_type}()", output)
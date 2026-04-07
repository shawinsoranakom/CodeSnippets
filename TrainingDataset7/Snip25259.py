def test_composite_primary_key_not_unique_together(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_compositepkmodel", stdout=out)
        self.assertNotIn("unique_together", out.getvalue())
def test_char_field_unlimited(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_charfieldunlimited", stdout=out)
        output = out.getvalue()
        self.assertIn("char_field = models.CharField()", output)
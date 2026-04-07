def test_decimal_field_no_precision(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_decimalfieldnoprec", stdout=out)
        output = out.getvalue()
        self.assertIn("decimal_field_no_precision = models.DecimalField()", output)
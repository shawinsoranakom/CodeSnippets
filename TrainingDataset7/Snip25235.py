def test_char_field_db_collation(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_charfielddbcollation", stdout=out)
        output = out.getvalue()
        if not connection.features.interprets_empty_strings_as_nulls:
            self.assertIn(
                "char_field = models.CharField(max_length=10, "
                "db_collation='%s')" % test_collation,
                output,
            )
        else:
            self.assertIn(
                "char_field = models.CharField(max_length=10, "
                "db_collation='%s', blank=True, null=True)" % test_collation,
                output,
            )
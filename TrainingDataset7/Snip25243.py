def test_digits_column_name_introspection(self):
        """
        Introspection of column names consist/start with digits (#16536/#17676)
        """
        char_field_type = connection.features.introspected_field_types["CharField"]
        out = StringIO()
        call_command("inspectdb", "inspectdb_digitsincolumnname", stdout=out)
        output = out.getvalue()
        error_message = "inspectdb generated a model field name which is a number"
        self.assertNotIn(
            "    123 = models.%s" % char_field_type, output, msg=error_message
        )
        self.assertIn("number_123 = models.%s" % char_field_type, output)

        error_message = (
            "inspectdb generated a model field name which starts with a digit"
        )
        self.assertNotIn(
            "    4extra = models.%s" % char_field_type, output, msg=error_message
        )
        self.assertIn("number_4extra = models.%s" % char_field_type, output)

        self.assertNotIn(
            "    45extra = models.%s" % char_field_type, output, msg=error_message
        )
        self.assertIn("number_45extra = models.%s" % char_field_type, output)
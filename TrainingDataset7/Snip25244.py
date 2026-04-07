def test_special_column_name_introspection(self):
        """
        Introspection of column names containing special characters,
        unsuitable for Python identifiers
        """
        out = StringIO()
        call_command("inspectdb", table_name_filter=special_table_only, stdout=out)
        output = out.getvalue()
        base_name = connection.introspection.identifier_converter("Field")
        integer_field_type = connection.features.introspected_field_types[
            "IntegerField"
        ]
        self.assertIn("field = models.%s()" % integer_field_type, output)
        self.assertIn(
            "field_field = models.%s(db_column='%s_')"
            % (integer_field_type, base_name),
            output,
        )
        self.assertIn(
            "field_field_0 = models.%s(db_column='%s__')"
            % (integer_field_type, base_name),
            output,
        )
        self.assertIn(
            "field_field_1 = models.%s(db_column='__field')" % integer_field_type,
            output,
        )
        self.assertIn(
            "prc_x = models.{}(db_column='prc(%) x')".format(integer_field_type), output
        )
        self.assertIn("tamaño = models.%s()" % integer_field_type, output)
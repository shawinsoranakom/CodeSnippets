def make_field_type_asserter(self):
        """
        Call inspectdb and return a function to validate a field type in its
        output.
        """
        out = StringIO()
        call_command("inspectdb", "inspectdb_columntypes", stdout=out)
        output = out.getvalue()

        def assertFieldType(name, definition):
            out_def = re.search(r"^\s*%s = (models.*)$" % name, output, re.MULTILINE)[1]
            self.assertEqual(definition, out_def)

        return assertFieldType
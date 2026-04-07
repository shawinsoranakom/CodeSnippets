def test_stealth_table_name_filter_option(self):
        out = StringIO()
        call_command("inspectdb", table_name_filter=inspectdb_tables_only, stdout=out)
        error_message = (
            "inspectdb has examined a table that should have been filtered out."
        )
        # contrib.contenttypes is one of the apps always installed when running
        # the Django test suite, check that one of its tables hasn't been
        # inspected
        self.assertNotIn(
            "class DjangoContentType(models.Model):", out.getvalue(), msg=error_message
        )
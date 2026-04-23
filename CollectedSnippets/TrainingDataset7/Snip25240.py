def test_attribute_name_not_python_keyword(self):
        out = StringIO()
        call_command("inspectdb", table_name_filter=inspectdb_tables_only, stdout=out)
        output = out.getvalue()
        error_message = (
            "inspectdb generated an attribute name which is a Python keyword"
        )
        # Recursive foreign keys should be set to 'self'
        self.assertIn("parent = models.ForeignKey('self', models.DO_NOTHING)", output)
        self.assertNotIn(
            "from = models.ForeignKey(InspectdbPeople, models.DO_NOTHING)",
            output,
            msg=error_message,
        )
        # As InspectdbPeople model is defined after InspectdbMessage, it should
        # be quoted.
        self.assertIn(
            "from_field = models.ForeignKey('InspectdbPeople', models.DO_NOTHING, "
            "db_column='from_id')",
            output,
        )
        self.assertIn(
            "people_pk = models.OneToOneField(InspectdbPeople, models.DO_NOTHING, "
            "primary_key=True)",
            output,
        )
        self.assertIn(
            "people_unique = models.OneToOneField(InspectdbPeople, models.DO_NOTHING)",
            output,
        )
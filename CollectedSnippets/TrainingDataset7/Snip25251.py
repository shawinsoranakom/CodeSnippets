def test_custom_fields(self):
        """
        Introspection of columns with a custom field (#21090)
        """
        out = StringIO()
        with mock.patch(
            "django.db.connection.introspection.data_types_reverse."
            "base_data_types_reverse",
            {
                "text": "myfields.TextField",
                "bigint": "BigIntegerField",
            },
        ):
            call_command("inspectdb", "inspectdb_columntypes", stdout=out)
            output = out.getvalue()
            self.assertIn("text_field = myfields.TextField()", output)
            self.assertIn("big_int_field = models.BigIntegerField()", output)
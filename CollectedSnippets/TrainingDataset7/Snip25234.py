def test_db_comments(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_dbcomment", stdout=out)
        output = out.getvalue()
        integer_field_type = connection.features.introspected_field_types[
            "IntegerField"
        ]
        self.assertIn(
            f"rank = models.{integer_field_type}("
            f"db_comment=\"'Rank' column comment\")",
            output,
        )
        self.assertIn(
            "        db_table_comment = 'Custom table comment'",
            output,
        )
def test_db_table_comment(self):
        class Model(models.Model):
            class Meta:
                db_table_comment = "Table comment"

        errors = Model.check(databases=self.databases)
        expected = (
            []
            if connection.features.supports_comments
            else [
                Warning(
                    f"{connection.display_name} does not support comments on tables "
                    f"(db_table_comment).",
                    obj=Model,
                    id="models.W046",
                ),
            ]
        )
        self.assertEqual(errors, expected)
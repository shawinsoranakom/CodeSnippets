def test_db_comment(self):
        class Model(models.Model):
            field = models.IntegerField(db_comment="Column comment")

        errors = Model._meta.get_field("field").check(databases=self.databases)
        expected = (
            []
            if connection.features.supports_comments
            else [
                DjangoWarning(
                    f"{connection.display_name} does not support comments on columns "
                    f"(db_comment).",
                    obj=Model._meta.get_field("field"),
                    id="fields.W163",
                ),
            ]
        )
        self.assertEqual(errors, expected)
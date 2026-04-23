def test_database_default(self):
        models.UniqueConstraint(
            fields=["field_with_db_default"], name="unique_field_with_db_default"
        ).validate(ModelWithDatabaseDefault, ModelWithDatabaseDefault())
        models.UniqueConstraint(
            Upper("field_with_db_default"),
            name="unique_field_with_db_default_expression",
        ).validate(ModelWithDatabaseDefault, ModelWithDatabaseDefault())

        ModelWithDatabaseDefault.objects.create()

        msg = (
            "Model with database default with this Field with db default already "
            "exists."
        )
        with self.assertRaisesMessage(ValidationError, msg):
            models.UniqueConstraint(
                fields=["field_with_db_default"], name="unique_field_with_db_default"
            ).validate(ModelWithDatabaseDefault, ModelWithDatabaseDefault())

        msg = "Constraint “unique_field_with_db_default_expression” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            models.UniqueConstraint(
                Upper("field_with_db_default"),
                name="unique_field_with_db_default_expression",
            ).validate(ModelWithDatabaseDefault, ModelWithDatabaseDefault())
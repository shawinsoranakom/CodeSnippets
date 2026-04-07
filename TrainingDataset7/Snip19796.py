def test_database_default(self):
        models.CheckConstraint(
            condition=models.Q(field_with_db_default="field_with_db_default"),
            name="check_field_with_db_default",
        ).validate(ModelWithDatabaseDefault, ModelWithDatabaseDefault())

        # Ensure that a check also does not silently pass with either
        # FieldError or DatabaseError when checking with a db_default.
        with self.assertRaises(ValidationError):
            models.CheckConstraint(
                condition=models.Q(
                    field_with_db_default="field_with_db_default", field="field"
                ),
                name="check_field_with_db_default_2",
            ).validate(
                ModelWithDatabaseDefault, ModelWithDatabaseDefault(field="not-field")
            )

        with self.assertRaises(ValidationError):
            models.CheckConstraint(
                condition=models.Q(field_with_db_default="field_with_db_default"),
                name="check_field_with_db_default",
            ).validate(
                ModelWithDatabaseDefault,
                ModelWithDatabaseDefault(field_with_db_default="other value"),
            )
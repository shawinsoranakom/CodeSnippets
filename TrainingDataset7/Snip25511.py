def test_db_default_expression_required_db_features(self):
        expression = models.F("field_name")

        class Model(models.Model):
            field = models.FloatField(db_default=expression)

            class Meta:
                required_db_features = {"supports_expression_defaults"}

        field = Model._meta.get_field("field")
        errors = field.check(databases=self.databases)

        if connection.features.supports_expression_defaults:
            msg = f"{expression} cannot be used in db_default."
            expected_errors = [Error(msg=msg, obj=field, id="fields.E012")]
        else:
            expected_errors = []
        self.assertEqual(errors, expected_errors)
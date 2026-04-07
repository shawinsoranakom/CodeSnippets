def test_db_default(self):
        class Model(models.Model):
            field = models.FloatField(db_default=Pi())

        field = Model._meta.get_field("field")
        errors = field.check(databases=self.databases)

        if connection.features.supports_expression_defaults:
            expected_errors = []
        else:
            msg = (
                f"{connection.display_name} does not support default database values "
                "with expressions (db_default)."
            )
            expected_errors = [Error(msg=msg, obj=field, id="fields.E011")]
        self.assertEqual(errors, expected_errors)
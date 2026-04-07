def test_db_default_combined_invalid(self):
        expression = models.Value(4.5) + models.F("field_name")

        class Model(models.Model):
            field = models.FloatField(db_default=expression)

        field = Model._meta.get_field("field")
        errors = field.check(databases=self.databases)

        msg = f"{expression} cannot be used in db_default."
        expected_error = Error(msg=msg, obj=field, id="fields.E012")
        self.assertEqual(errors, [expected_error])
def test_output_field_charfield_unlimited_error(self):
        class Model(models.Model):
            name = models.CharField(max_length=255)
            field = models.GeneratedField(
                expression=LPad("name", 7, models.Value("xy")),
                output_field=models.CharField(),
                db_persist=True,
            )

        expected_errors = (
            []
            if connection.features.supports_unlimited_charfield
            else [
                Error(
                    "GeneratedField.output_field has errors:"
                    "\n    CharFields must define a 'max_length' attribute. "
                    "(fields.E120)",
                    obj=Model._meta.get_field("field"),
                    id="fields.E223",
                ),
            ]
        )
        self.assertEqual(
            Model._meta.get_field("field").check(databases={"default"}),
            expected_errors,
        )
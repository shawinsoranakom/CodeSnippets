def test_output_field_check_error(self):
        class Model(models.Model):
            value = models.DecimalField(max_digits=5, decimal_places=2)
            field = models.GeneratedField(
                expression=models.F("value") * 2,
                output_field=models.DecimalField(max_digits=-1, decimal_places=-1),
                db_persist=True,
            )

        expected_errors = [
            Error(
                "GeneratedField.output_field has errors:"
                "\n    'decimal_places' must be a non-negative integer. (fields.E131)"
                "\n    'max_digits' must be a positive integer. (fields.E133)",
                obj=Model._meta.get_field("field"),
                id="fields.E223",
            ),
        ]
        self.assertEqual(
            Model._meta.get_field("field").check(databases={"default"}),
            expected_errors,
        )
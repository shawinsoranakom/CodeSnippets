def test_output_field_check_warning(self):
        class Model(models.Model):
            value = models.IntegerField()
            field = models.GeneratedField(
                expression=models.F("value") * 2,
                output_field=models.IntegerField(max_length=40),
                db_persist=True,
            )

        expected_warnings = [
            DjangoWarning(
                "GeneratedField.output_field has warnings:"
                "\n    'max_length' is ignored when used with IntegerField. "
                "(fields.W122)",
                obj=Model._meta.get_field("field"),
                id="fields.W224",
            ),
        ]
        self.assertEqual(
            Model._meta.get_field("field").check(databases={"default"}),
            expected_warnings,
        )
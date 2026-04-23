def test_with_null_argument(self):
        class Model(models.Model):
            value = models.IntegerField()
            field = models.GeneratedField(
                expression=models.F("value") * 2,
                output_field=models.IntegerField(),
                db_persist=True,
                null=True,
            )

        expected_warnings = [
            DjangoWarning(
                "null has no effect on GeneratedField.",
                obj=Model._meta.get_field("field"),
                id="fields.W225",
            ),
        ]
        self.assertEqual(
            Model._meta.get_field("field").check(databases={"default"}),
            expected_warnings,
        )
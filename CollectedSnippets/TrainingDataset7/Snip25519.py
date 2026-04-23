def test_not_supported_stored(self):
        class Model(models.Model):
            name = models.IntegerField()
            field = models.GeneratedField(
                expression=models.F("name"),
                output_field=models.IntegerField(),
                db_persist=True,
            )
            a = models.TextField()

        expected_errors = (
            []
            if connection.features.supports_stored_generated_columns
            else [
                Error(
                    f"{connection.display_name} does not support persisted "
                    "GeneratedFields.",
                    obj=Model._meta.get_field("field"),
                    id="fields.E222",
                    hint="Set db_persist=False on the field.",
                ),
            ]
        )
        self.assertEqual(
            Model._meta.get_field("field").check(databases={"default"}),
            expected_errors,
        )
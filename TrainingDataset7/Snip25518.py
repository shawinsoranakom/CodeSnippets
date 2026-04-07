def test_not_supported_virtual(self):
        class Model(models.Model):
            name = models.IntegerField()
            field = models.GeneratedField(
                expression=models.F("name"),
                output_field=models.IntegerField(),
                db_persist=False,
            )
            a = models.TextField()

        excepted_errors = (
            []
            if connection.features.supports_virtual_generated_columns
            else [
                Error(
                    f"{connection.display_name} does not support non-persisted "
                    "GeneratedFields.",
                    obj=Model._meta.get_field("field"),
                    id="fields.E221",
                    hint="Set db_persist=True on the field.",
                ),
            ]
        )
        self.assertEqual(
            Model._meta.get_field("field").check(databases={"default"}),
            excepted_errors,
        )
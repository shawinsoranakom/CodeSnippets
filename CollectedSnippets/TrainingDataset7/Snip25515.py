def test_not_supported(self):
        db_persist = connection.features.supports_stored_generated_columns

        class Model(models.Model):
            name = models.IntegerField()
            field = models.GeneratedField(
                expression=models.F("name"),
                output_field=models.IntegerField(),
                db_persist=db_persist,
            )

        expected_errors = []
        if (
            not connection.features.supports_stored_generated_columns
            and not connection.features.supports_virtual_generated_columns
        ):
            expected_errors.append(
                Error(
                    f"{connection.display_name} does not support GeneratedFields.",
                    obj=Model._meta.get_field("field"),
                    id="fields.E220",
                )
            )
        if (
            not db_persist
            and not connection.features.supports_virtual_generated_columns
        ):
            expected_errors.append(
                Error(
                    f"{connection.display_name} does not support non-persisted "
                    "GeneratedFields.",
                    obj=Model._meta.get_field("field"),
                    id="fields.E221",
                    hint="Set db_persist=True on the field.",
                ),
            )
        self.assertEqual(
            Model._meta.get_field("field").check(databases={"default"}),
            expected_errors,
        )
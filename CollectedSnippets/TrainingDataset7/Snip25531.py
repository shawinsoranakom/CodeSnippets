def test_foreign_key_to_missing_model(self):
        # Model names are resolved when a model is being created, so we cannot
        # test relative fields in isolation and we need to attach them to a
        # model.
        class Model(models.Model):
            foreign_key = models.ForeignKey("Rel1", models.CASCADE)

        field = Model._meta.get_field("foreign_key")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "Field defines a relation with model 'Rel1', "
                    "which is either not installed, or is abstract.",
                    obj=field,
                    id="fields.E300",
                ),
            ],
        )
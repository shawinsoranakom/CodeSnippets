def test_pointing_to_missing_model(self):
        class Model(models.Model):
            rel = GenericRelation("MissingModel")

        self.assertEqual(
            Model.rel.field.check(),
            [
                checks.Error(
                    "Field defines a relation with model 'MissingModel', "
                    "which is either not installed, or is abstract.",
                    obj=Model.rel.field,
                    id="fields.E300",
                )
            ],
        )
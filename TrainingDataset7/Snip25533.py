def test_many_to_many_to_missing_model(self):
        class Model(models.Model):
            m2m = models.ManyToManyField("Rel2")

        field = Model._meta.get_field("m2m")
        self.assertEqual(
            field.check(from_model=Model),
            [
                Error(
                    "Field defines a relation with model 'Rel2', "
                    "which is either not installed, or is abstract.",
                    obj=field,
                    id="fields.E300",
                ),
            ],
        )
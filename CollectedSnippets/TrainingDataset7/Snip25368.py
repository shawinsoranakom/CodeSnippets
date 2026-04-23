def test_property_and_related_field_accessor_clash(self):
        class Model(models.Model):
            fk = models.ForeignKey("self", models.CASCADE)

        # Override related field accessor.
        Model.fk_id = property(lambda self: "ERROR")

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "The property 'fk_id' clashes with a related field accessor.",
                    obj=Model,
                    id="models.E025",
                )
            ],
        )
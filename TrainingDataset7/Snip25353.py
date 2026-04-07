def test_non_valid(self):
        class RelationModel(models.Model):
            pass

        class Model(models.Model):
            relation = models.ManyToManyField(RelationModel)

            class Meta:
                ordering = ["relation"]

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'ordering' refers to the nonexistent field, related field, "
                    "or lookup 'relation'.",
                    obj=Model,
                    id="models.E015",
                ),
            ],
        )
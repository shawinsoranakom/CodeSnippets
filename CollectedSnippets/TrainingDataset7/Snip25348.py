def test_unique_primary_key(self):
        invalid_id = models.IntegerField(primary_key=False)

        class Model(models.Model):
            id = invalid_id

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'id' can only be used as a field name if the field also sets "
                    "'primary_key=True'.",
                    obj=Model,
                    id="models.E004",
                ),
            ],
        )
def test_single_primary_key(self):
        class Model(models.Model):
            foo = models.IntegerField(primary_key=True)
            bar = models.IntegerField(primary_key=True)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "The model cannot have more than one field with "
                    "'primary_key=True'.",
                    obj=Model,
                    id="models.E026",
                )
            ],
        )
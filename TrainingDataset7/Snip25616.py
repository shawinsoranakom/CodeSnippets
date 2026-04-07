def test_valid_model(self):
        class Model(models.Model):
            first = models.ManyToManyField(
                "self", symmetrical=False, related_name="first_accessor"
            )
            second = models.ManyToManyField(
                "self", symmetrical=False, related_name="second_accessor"
            )

        self.assertEqual(Model.check(), [])
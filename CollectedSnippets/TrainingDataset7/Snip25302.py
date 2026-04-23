def test_valid_model(self):
        class Model(models.Model):
            one = models.IntegerField()
            two = models.IntegerField()

            class Meta:
                # unique_together can be a simple tuple
                unique_together = ("one", "two")

        self.assertEqual(Model.check(), [])
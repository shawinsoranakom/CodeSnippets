def test_invalid_to_parameter(self):
        msg = (
            "ForeignKey(1) is invalid. First parameter to ForeignKey must be "
            "either a model, a model name, or the string 'self'"
        )
        with self.assertRaisesMessage(TypeError, msg):

            class MyModel(models.Model):
                child = models.ForeignKey(1, models.CASCADE)
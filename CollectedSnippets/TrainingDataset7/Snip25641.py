def _test():
            # Define model with the same name.
            class Model(models.Model):
                m2m = models.ManyToManyField(Target, related_name="+")

                class Meta:
                    app_label = "invalid_models_tests"

            self.assertEqual(Model.check(), [])
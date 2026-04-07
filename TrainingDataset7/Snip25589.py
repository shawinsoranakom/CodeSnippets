def test_no_clash_across_apps_without_accessor(self):
        class Target(models.Model):
            class Meta:
                app_label = "invalid_models_tests"

        class Model(models.Model):
            m2m = models.ManyToManyField(Target, related_name="+")

            class Meta:
                app_label = "basic"

        def _test():
            # Define model with the same name.
            class Model(models.Model):
                m2m = models.ManyToManyField(Target, related_name="+")

                class Meta:
                    app_label = "invalid_models_tests"

            self.assertEqual(Model.check(), [])

        _test()
        self.assertEqual(Model.check(), [])
def _test_accessor_clash(self, target, relative):
        class Another(models.Model):
            pass

        class Target(models.Model):
            model_set = target

        class Model(models.Model):
            rel = relative

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse accessor 'Target.model_set' for "
                    "'invalid_models_tests.Model.rel' clashes with field name "
                    "'invalid_models_tests.Target.model_set'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Target.model_set', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.rel'."
                    ),
                    obj=Model._meta.get_field("rel"),
                    id="fields.E302",
                ),
            ],
        )
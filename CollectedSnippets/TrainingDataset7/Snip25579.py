def test_clash_between_accessors(self):
        class Target(models.Model):
            pass

        class Model(models.Model):
            foreign = models.ForeignKey(Target, models.CASCADE)
            m2m = models.ManyToManyField(Target)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse accessor 'Target.model_set' for "
                    "'invalid_models_tests.Model.foreign' clashes with reverse "
                    "accessor for 'invalid_models_tests.Model.m2m'.",
                    hint=(
                        "Add or change a related_name argument to the definition "
                        "for 'invalid_models_tests.Model.foreign' or "
                        "'invalid_models_tests.Model.m2m'."
                    ),
                    obj=Model._meta.get_field("foreign"),
                    id="fields.E304",
                ),
                Error(
                    "Reverse accessor 'Target.model_set' for "
                    "'invalid_models_tests.Model.m2m' clashes with reverse "
                    "accessor for 'invalid_models_tests.Model.foreign'.",
                    hint=(
                        "Add or change a related_name argument to the definition "
                        "for 'invalid_models_tests.Model.m2m' or "
                        "'invalid_models_tests.Model.foreign'."
                    ),
                    obj=Model._meta.get_field("m2m"),
                    id="fields.E304",
                ),
            ],
        )
def test_clash_between_accessors(self):
        class Model(models.Model):
            first_m2m = models.ManyToManyField("self", symmetrical=False)
            second_m2m = models.ManyToManyField("self", symmetrical=False)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse accessor 'Model.model_set' for "
                    "'invalid_models_tests.Model.first_m2m' clashes with reverse "
                    "accessor for 'invalid_models_tests.Model.second_m2m'.",
                    hint=(
                        "Add or change a related_name argument to the definition "
                        "for 'invalid_models_tests.Model.first_m2m' or "
                        "'invalid_models_tests.Model.second_m2m'."
                    ),
                    obj=Model._meta.get_field("first_m2m"),
                    id="fields.E304",
                ),
                Error(
                    "Reverse accessor 'Model.model_set' for "
                    "'invalid_models_tests.Model.second_m2m' clashes with reverse "
                    "accessor for 'invalid_models_tests.Model.first_m2m'.",
                    hint=(
                        "Add or change a related_name argument to the definition "
                        "for 'invalid_models_tests.Model.second_m2m' or "
                        "'invalid_models_tests.Model.first_m2m'."
                    ),
                    obj=Model._meta.get_field("second_m2m"),
                    id="fields.E304",
                ),
            ],
        )
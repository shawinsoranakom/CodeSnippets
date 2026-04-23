def test_accessor_clash(self):
        class Model(models.Model):
            model_set = models.ForeignKey("Model", models.CASCADE)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse accessor 'Model.model_set' for "
                    "'invalid_models_tests.Model.model_set' clashes with field "
                    "name 'invalid_models_tests.Model.model_set'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Model.model_set', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.model_set'."
                    ),
                    obj=Model._meta.get_field("model_set"),
                    id="fields.E302",
                ),
            ],
        )
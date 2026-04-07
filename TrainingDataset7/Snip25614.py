def test_reverse_query_name_clash(self):
        class Model(models.Model):
            model = models.ManyToManyField("self", symmetrical=False)

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse query name for 'invalid_models_tests.Model.model' "
                    "clashes with field name 'invalid_models_tests.Model.model'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Model.model', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.model'."
                    ),
                    obj=Model._meta.get_field("model"),
                    id="fields.E303",
                ),
            ],
        )
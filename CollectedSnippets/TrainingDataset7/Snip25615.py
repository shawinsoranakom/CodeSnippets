def test_clash_under_explicit_related_name(self):
        class Model(models.Model):
            clash = models.IntegerField()
            m2m = models.ManyToManyField(
                "self", symmetrical=False, related_name="clash"
            )

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse accessor 'Model.clash' for "
                    "'invalid_models_tests.Model.m2m' clashes with field name "
                    "'invalid_models_tests.Model.clash'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Model.clash', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.m2m'."
                    ),
                    obj=Model._meta.get_field("m2m"),
                    id="fields.E302",
                ),
                Error(
                    "Reverse query name for 'invalid_models_tests.Model.m2m' "
                    "clashes with field name 'invalid_models_tests.Model.clash'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Model.clash', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.m2m'."
                    ),
                    obj=Model._meta.get_field("m2m"),
                    id="fields.E303",
                ),
            ],
        )
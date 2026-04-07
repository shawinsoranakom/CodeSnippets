def _test_explicit_related_name_clash(self, target, relative):
        class Another(models.Model):
            pass

        class Target(models.Model):
            clash = target

        class Model(models.Model):
            rel = relative

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse accessor 'Target.clash' for "
                    "'invalid_models_tests.Model.rel' clashes with field name "
                    "'invalid_models_tests.Target.clash'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Target.clash', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.rel'."
                    ),
                    obj=Model._meta.get_field("rel"),
                    id="fields.E302",
                ),
                Error(
                    "Reverse query name for 'invalid_models_tests.Model.rel' "
                    "clashes with field name 'invalid_models_tests.Target.clash'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Target.clash', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.rel'."
                    ),
                    obj=Model._meta.get_field("rel"),
                    id="fields.E303",
                ),
            ],
        )
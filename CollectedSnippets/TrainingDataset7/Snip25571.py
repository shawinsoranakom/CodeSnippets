def test_invalid_related_query_name(self):
        class Target(models.Model):
            pass

        class Model(models.Model):
            first = models.ForeignKey(
                Target, models.CASCADE, related_name="contains__double"
            )
            second = models.ForeignKey(
                Target, models.CASCADE, related_query_name="ends_underscore_"
            )

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse query name 'contains__double' must not contain '__'.",
                    hint=(
                        "Add or change a related_name or related_query_name "
                        "argument for this field."
                    ),
                    obj=Model._meta.get_field("first"),
                    id="fields.E309",
                ),
                Error(
                    "Reverse query name 'ends_underscore_' must not end with an "
                    "underscore.",
                    hint=(
                        "Add or change a related_name or related_query_name "
                        "argument for this field."
                    ),
                    obj=Model._meta.get_field("second"),
                    id="fields.E308",
                ),
            ],
        )
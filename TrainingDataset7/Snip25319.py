def test_index_with_include(self):
        class Model(models.Model):
            age = models.IntegerField()

            class Meta:
                indexes = [
                    models.Index(
                        fields=["age"],
                        name="index_age_include_id",
                        include=["id"],
                    ),
                ]

        errors = Model.check(databases=self.databases)
        expected = (
            []
            if connection.features.supports_covering_indexes
            else [
                Warning(
                    "%s does not support indexes with non-key columns."
                    % connection.display_name,
                    hint=(
                        "Non-key columns will be ignored. Silence this warning if "
                        "you don't care about it."
                    ),
                    obj=Model,
                    id="models.W040",
                )
            ]
        )
        self.assertEqual(errors, expected)
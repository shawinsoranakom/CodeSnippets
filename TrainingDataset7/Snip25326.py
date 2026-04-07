def test_func_index(self):
        class Model(models.Model):
            name = models.CharField(max_length=10)

            class Meta:
                indexes = [models.Index(Lower("name"), name="index_lower_name")]

        warn = Warning(
            "%s does not support indexes on expressions." % connection.display_name,
            hint=(
                "An index won't be created. Silence this warning if you don't "
                "care about it."
            ),
            obj=Model,
            id="models.W043",
        )
        expected = [] if connection.features.supports_expression_indexes else [warn]
        self.assertEqual(Model.check(databases=self.databases), expected)
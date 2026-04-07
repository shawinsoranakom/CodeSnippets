def test_nullbooleanfield_deprecated(self):
        class NullBooleanFieldModel(models.Model):
            nb = models.NullBooleanField()

        model = NullBooleanFieldModel()
        self.assertEqual(
            model.check(),
            [
                checks.Error(
                    "NullBooleanField is removed except for support in historical "
                    "migrations.",
                    hint="Use BooleanField(null=True, blank=True) instead.",
                    obj=NullBooleanFieldModel._meta.get_field("nb"),
                    id="fields.E903",
                ),
            ],
        )
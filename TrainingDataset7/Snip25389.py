def test_ordering_pointing_to_json_field_value(self):
        class Model(models.Model):
            field = models.JSONField()

            class Meta:
                ordering = ["field__value"]

        self.assertEqual(Model.check(databases=self.databases), [])
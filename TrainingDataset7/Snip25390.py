def test_check_jsonfield(self):
        class Model(models.Model):
            field = models.JSONField()

        error = Error(
            "%s does not support JSONFields." % connection.display_name,
            obj=Model,
            id="fields.E180",
        )
        expected = [] if connection.features.supports_json_field else [error]
        self.assertEqual(Model.check(databases=self.databases), expected)
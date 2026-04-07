def test_check_jsonfield_required_db_features(self):
        class Model(models.Model):
            field = models.JSONField()

            class Meta:
                required_db_features = {"supports_json_field"}

        self.assertEqual(Model.check(databases=self.databases), [])
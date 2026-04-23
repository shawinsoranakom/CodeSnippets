def test_not_supported_stored_required_db_features(self):
        class Model(models.Model):
            name = models.IntegerField()
            field = models.GeneratedField(
                expression=models.F("name"),
                output_field=models.IntegerField(),
                db_persist=True,
            )

            class Meta:
                required_db_features = {"supports_stored_generated_columns"}

        self.assertEqual(Model.check(databases=self.databases), [])
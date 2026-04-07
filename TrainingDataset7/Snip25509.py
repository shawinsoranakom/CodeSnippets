def test_db_default_required_db_features(self):
        class Model(models.Model):
            field = models.FloatField(db_default=Pi())

            class Meta:
                required_db_features = {"supports_expression_defaults"}

        field = Model._meta.get_field("field")
        errors = field.check(databases=self.databases)
        self.assertEqual(errors, [])
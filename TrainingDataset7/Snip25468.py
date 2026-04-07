def test_db_collation_required_db_features(self):
        class Model(models.Model):
            field = models.CharField(max_length=100, db_collation="anything")

            class Meta:
                required_db_features = {"supports_collation_on_charfield"}

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(databases=self.databases), [])
def test_db_collation_required_db_features(self):
        class Model(models.Model):
            field = models.TextField(db_collation="anything")

            class Meta:
                required_db_features = {"supports_collation_on_textfield"}

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(databases=self.databases), [])
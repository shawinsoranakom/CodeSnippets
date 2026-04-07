def test_both_attributes_omitted_required_db_features(self):
        class Model(models.Model):
            field = models.DecimalField()

            class Meta:
                required_db_features = {"supports_no_precision_decimalfield"}

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(databases=self.databases), [])
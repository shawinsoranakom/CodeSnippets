def test_both_attributes_omitted(self):
        class Model(models.Model):
            field = models.DecimalField()

        field = Model._meta.get_field("field")
        if connection.features.supports_no_precision_decimalfield:
            expected = []
        else:
            expected = [
                Error(
                    "DecimalFields must define a 'decimal_places' attribute.",
                    obj=field,
                    id="fields.E130",
                ),
                Error(
                    "DecimalFields must define a 'max_digits' attribute.",
                    obj=field,
                    id="fields.E132",
                ),
            ]
        self.assertEqual(field.check(databases=self.databases), expected)
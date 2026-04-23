def test_valid_field(self):
        class Model(models.Model):
            field = models.DecimalField(max_digits=10, decimal_places=10)

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(databases=self.databases), [])
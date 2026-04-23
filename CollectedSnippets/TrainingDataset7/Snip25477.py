def test_only_decimal_places_defined(self):
        class Model(models.Model):
            field = models.DecimalField(decimal_places=5)

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(databases=self.databases),
            [
                Error(
                    "DecimalField’s max_digits and decimal_places must both "
                    "be defined or both omitted.",
                    obj=field,
                    id="fields.E135",
                ),
            ],
        )
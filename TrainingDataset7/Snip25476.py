def test_only_max_digits_defined(self):
        class Model(models.Model):
            field = models.DecimalField(max_digits=13)

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
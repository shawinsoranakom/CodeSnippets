def test_max_length_warning(self):
        class Model(models.Model):
            integer = models.IntegerField(max_length=2)
            biginteger = models.BigIntegerField(max_length=2)
            smallinteger = models.SmallIntegerField(max_length=2)
            positiveinteger = models.PositiveIntegerField(max_length=2)
            positivebiginteger = models.PositiveBigIntegerField(max_length=2)
            positivesmallinteger = models.PositiveSmallIntegerField(max_length=2)

        for field in Model._meta.get_fields():
            if field.auto_created:
                continue
            with self.subTest(name=field.name):
                self.assertEqual(
                    field.check(),
                    [
                        DjangoWarning(
                            "'max_length' is ignored when used with %s."
                            % field.__class__.__name__,
                            hint="Remove 'max_length' from field",
                            obj=field,
                            id="fields.W122",
                        )
                    ],
                )
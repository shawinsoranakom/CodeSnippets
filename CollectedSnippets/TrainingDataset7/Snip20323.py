def test_cast_to_integer(self):
        for field_class in (
            models.AutoField,
            models.BigAutoField,
            models.SmallAutoField,
            models.IntegerField,
            models.BigIntegerField,
            models.SmallIntegerField,
            models.PositiveBigIntegerField,
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
        ):
            with self.subTest(field_class=field_class):
                numbers = Author.objects.annotate(cast_int=Cast("alias", field_class()))
                self.assertEqual(numbers.get().cast_int, 1)
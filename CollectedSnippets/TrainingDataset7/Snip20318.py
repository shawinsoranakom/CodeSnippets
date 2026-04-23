def test_cast_from_value(self):
        numbers = Author.objects.annotate(
            cast_integer=Cast(models.Value("0"), models.IntegerField())
        )
        self.assertEqual(numbers.get().cast_integer, 0)
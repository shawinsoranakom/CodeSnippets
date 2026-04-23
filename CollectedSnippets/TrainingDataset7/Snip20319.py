def test_cast_from_field(self):
        numbers = Author.objects.annotate(
            cast_string=Cast("age", models.CharField(max_length=255)),
        )
        self.assertEqual(numbers.get().cast_string, "1")
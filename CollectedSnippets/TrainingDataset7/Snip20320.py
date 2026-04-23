def test_cast_to_char_field_without_max_length(self):
        numbers = Author.objects.annotate(cast_string=Cast("age", models.CharField()))
        self.assertEqual(numbers.get().cast_string, "1")
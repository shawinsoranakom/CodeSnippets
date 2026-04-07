def test_cast_to_char_field_with_max_length(self):
        names = Author.objects.annotate(
            cast_string=Cast("name", models.CharField(max_length=1))
        )
        self.assertEqual(names.get().cast_string, "B")
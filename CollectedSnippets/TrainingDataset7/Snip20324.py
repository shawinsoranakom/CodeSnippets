def test_cast_to_integer_foreign_key(self):
        numbers = Author.objects.annotate(
            cast_fk=Cast(
                models.Value("0"),
                models.ForeignKey(Author, on_delete=models.SET_NULL),
            )
        )
        self.assertEqual(numbers.get().cast_fk, 0)
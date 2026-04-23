def test_null(self):
        author = Author.objects.annotate(backward=Reverse("alias")).get(
            pk=self.python.pk
        )
        self.assertEqual(
            author.backward,
            "" if connection.features.interprets_empty_strings_as_nulls else None,
        )
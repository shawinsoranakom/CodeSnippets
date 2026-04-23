def test_basic_alias_f_annotation(self):
        qs = Book.objects.alias(another_rating_alias=F("rating")).annotate(
            another_rating=F("another_rating_alias")
        )
        self.assertIs(hasattr(qs.first(), "another_rating_alias"), False)
        for book in qs:
            with self.subTest(book=book):
                self.assertEqual(book.another_rating, book.rating)
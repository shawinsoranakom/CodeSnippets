def test_basic_alias_f_transform_annotation(self):
        qs = Book.objects.alias(
            pubdate_alias=F("pubdate"),
        ).annotate(pubdate_year=F("pubdate_alias__year"))
        self.assertIs(hasattr(qs.first(), "pubdate_alias"), False)
        for book in qs:
            with self.subTest(book=book):
                self.assertEqual(book.pubdate_year, book.pubdate.year)
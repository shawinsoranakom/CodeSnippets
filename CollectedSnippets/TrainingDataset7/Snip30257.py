def test_foreignkey_reverse(self):
        authors = Author.objects.order_by("-name")
        with self.assertNumQueries(3):
            books = list(
                Book.objects.prefetch_related(
                    Prefetch(
                        "first_time_authors",
                        authors,
                    ),
                    Prefetch(
                        "first_time_authors",
                        authors[1:],
                        to_attr="first_time_authors_sliced",
                    ),
                )
            )
        for book in books:
            with self.subTest(book=book):
                self.assertEqual(
                    book.first_time_authors_sliced,
                    list(book.first_time_authors.all())[1:],
                )
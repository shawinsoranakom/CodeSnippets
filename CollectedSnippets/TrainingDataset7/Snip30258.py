def test_reverse_ordering(self):
        authors = Author.objects.reverse()  # Reverse Meta.ordering
        with self.assertNumQueries(3):
            books = list(
                Book.objects.prefetch_related(
                    Prefetch("authors", authors),
                    Prefetch("authors", authors[1:], to_attr="authors_sliced"),
                )
            )
        for book in books:
            with self.subTest(book=book):
                self.assertEqual(book.authors_sliced, list(book.authors.all())[1:])
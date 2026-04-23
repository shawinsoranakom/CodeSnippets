def test_empty_order(self):
        authors = Author.objects.order_by()
        with self.assertNumQueries(3):
            books = list(
                Book.objects.prefetch_related(
                    Prefetch("authors", authors),
                    Prefetch("authors", authors[:1], to_attr="authors_sliced"),
                )
            )
        for book in books:
            with self.subTest(book=book):
                self.assertEqual(len(book.authors_sliced), 1)
                self.assertIn(book.authors_sliced[0], list(book.authors.all()))
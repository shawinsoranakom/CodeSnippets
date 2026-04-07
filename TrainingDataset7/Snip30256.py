def test_m2m_reverse(self):
        books = Book.objects.order_by("title")
        with self.assertNumQueries(3):
            authors = list(
                Author.objects.prefetch_related(
                    Prefetch("books", books),
                    Prefetch("books", books[1:2], to_attr="books_sliced"),
                )
            )
        for author in authors:
            with self.subTest(author=author):
                self.assertEqual(author.books_sliced, list(author.books.all())[1:2])
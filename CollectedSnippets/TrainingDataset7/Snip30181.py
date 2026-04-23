def test_basic(self):
        with self.assertNumQueries(2):
            books = Book.objects.raw(
                "SELECT * FROM prefetch_related_book WHERE id = %s", (self.book1.id,)
            ).prefetch_related("authors")
            book1 = list(books)[0]

        with self.assertNumQueries(0):
            self.assertCountEqual(
                book1.authors.all(), [self.author1, self.author2, self.author3]
            )
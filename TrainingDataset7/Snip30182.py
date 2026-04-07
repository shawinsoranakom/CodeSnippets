def test_prefetch_before_raw(self):
        with self.assertNumQueries(2):
            books = Book.objects.prefetch_related("authors").raw(
                "SELECT * FROM prefetch_related_book WHERE id = %s", (self.book1.id,)
            )
            book1 = list(books)[0]

        with self.assertNumQueries(0):
            self.assertCountEqual(
                book1.authors.all(), [self.author1, self.author2, self.author3]
            )
def test_m2m_forward(self):
        book1 = Book.objects.get(id=self.book1.id)
        with self.assertNumQueries(1):
            prefetch_related_objects([book1], "authors")

        with self.assertNumQueries(0):
            self.assertCountEqual(
                book1.authors.all(), [self.author1, self.author2, self.author3]
            )
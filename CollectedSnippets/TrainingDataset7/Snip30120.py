def test_m2m_reverse(self):
        author1 = Author.objects.get(id=self.author1.id)
        with self.assertNumQueries(1):
            prefetch_related_objects([author1], "books")

        with self.assertNumQueries(0):
            self.assertCountEqual(author1.books.all(), [self.book1, self.book2])
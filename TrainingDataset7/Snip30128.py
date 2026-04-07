def test_prefetch_object_to_attr(self):
        book1 = Book.objects.get(id=self.book1.id)
        with self.assertNumQueries(1):
            prefetch_related_objects(
                [book1], Prefetch("authors", to_attr="the_authors")
            )

        with self.assertNumQueries(0):
            self.assertCountEqual(
                book1.the_authors, [self.author1, self.author2, self.author3]
            )
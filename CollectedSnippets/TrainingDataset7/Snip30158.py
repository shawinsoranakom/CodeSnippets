def test_count(self):
        with self.assertNumQueries(2):
            qs = Book.objects.prefetch_related("first_time_authors")
            [b.first_time_authors.count() for b in qs]
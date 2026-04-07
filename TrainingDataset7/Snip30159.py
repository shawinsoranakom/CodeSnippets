def test_exists(self):
        with self.assertNumQueries(2):
            qs = Book.objects.prefetch_related("first_time_authors")
            [b.first_time_authors.exists() for b in qs]
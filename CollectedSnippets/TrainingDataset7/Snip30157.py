def test_bool(self):
        with self.assertNumQueries(2):
            qs = Book.objects.prefetch_related("first_time_authors")
            bool(qs)
            [list(b.first_time_authors.all()) for b in qs]
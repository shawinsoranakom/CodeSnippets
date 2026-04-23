def test_foreignkey_reverse(self):
        with self.assertNumQueries(2):
            [
                list(b.first_time_authors.all())
                for b in Book.objects.prefetch_related("first_time_authors")
            ]

        self.assertSequenceEqual(self.book2.authors.all(), [self.author1])
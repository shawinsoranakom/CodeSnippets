def test_survives_clone(self):
        with self.assertNumQueries(2):
            [
                list(b.first_time_authors.all())
                for b in Book.objects.prefetch_related("first_time_authors").exclude(
                    id=1000
                )
            ]
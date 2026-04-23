def test_parent_link_prefetch(self):
        with self.assertNumQueries(2):
            [a.author for a in AuthorWithAge.objects.prefetch_related("author")]
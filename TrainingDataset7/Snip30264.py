def test_parent_m2m_available_in_child(self):
        qs = (
            Author.objects.select_related("authorwithage")
            .prefetch_related("favorite_authors")
            .filter(pk=self.m2m_child.pk)
        )
        with self.assertNumQueries(2):
            results = list(qs)
            self.assertEqual(len(results), 1)
            self.assertQuerySetEqual(
                results[0].authorwithage.favorite_authors.all(),
                [self.related1, self.related2, self.related3],
            )
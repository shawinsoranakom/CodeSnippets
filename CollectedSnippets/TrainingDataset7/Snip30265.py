def test_grandparent_m2m_available_in_child(self):
        qs = (
            Author.objects.select_related(
                "authorwithage", "authorwithage__authorwithagechild"
            )
            .prefetch_related("favorite_authors")
            .filter(pk=self.m2m_child.pk)
        )
        with self.assertNumQueries(2):
            results = list(qs)
            self.assertEqual(len(results), 1)
            self.assertQuerySetEqual(
                set(results[0].authorwithage.authorwithagechild.favorite_authors.all()),
                {self.related1, self.related2, self.related3},
            )
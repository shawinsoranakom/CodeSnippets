def test_remove_clears_prefetched_objects_in_parent(self):
        gp = (
            Author.objects.select_related("authorwithage")
            .prefetch_related("favorite_authors")
            .get(pk=self.m2m_child.pk)
        )
        self.assertCountEqual(
            gp.favorite_authors.all(),
            [self.related1, self.related2, self.related3],
        )
        self.assertCountEqual(
            gp.authorwithage.favorite_authors.all(),
            [self.related1, self.related2, self.related3],
        )
        gp.authorwithage.favorite_authors.clear()
        self.assertSequenceEqual(gp.favorite_authors.all(), [])
        self.assertSequenceEqual(gp.authorwithage.favorite_authors.all(), [])
def test_add_clears_prefetched_objects_in_grandparent(self):
        gp = (
            Author.objects.select_related(
                "authorwithage", "authorwithage__authorwithagechild"
            )
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
        self.assertCountEqual(
            gp.authorwithage.authorwithagechild.favorite_authors.all(),
            [self.related1, self.related2, self.related3],
        )
        gp.authorwithage.authorwithagechild.favorite_authors.add(self.related4)
        self.assertCountEqual(
            gp.favorite_authors.all(),
            [self.related1, self.related2, self.related3, self.related4],
        )
        self.assertCountEqual(
            gp.authorwithage.favorite_authors.all(),
            [self.related1, self.related2, self.related3, self.related4],
        )
        self.assertCountEqual(
            gp.authorwithage.authorwithagechild.favorite_authors.all(),
            [self.related1, self.related2, self.related3, self.related4],
        )
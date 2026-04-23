def test_reverse_object_cached_when_related_is_accessed(self):
        """
        Regression for #13839 and #17439.

        The target of a one-to-one relation is cached
        when the origin is accessed through the reverse relation.
        """
        # Use a fresh object without caches
        r = Restaurant.objects.get(pk=self.r1.pk)
        p = r.place
        with self.assertNumQueries(0):
            self.assertEqual(p.restaurant, r)
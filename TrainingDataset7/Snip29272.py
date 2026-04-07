def test_related_object_cached_when_reverse_is_accessed(self):
        """
        Regression for #13839 and #17439.

        The origin of a one-to-one relation is cached
        when the target is accessed through the reverse relation.
        """
        # Use a fresh object without caches
        p = Place.objects.get(pk=self.p1.pk)
        r = p.restaurant
        with self.assertNumQueries(0):
            self.assertEqual(r.place, p)
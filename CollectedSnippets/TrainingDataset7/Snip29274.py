def test_reverse_object_cached_when_related_is_unset(self):
        """
        Regression for #13839 and #17439.

        The target of a one-to-one relation is always cached.
        """
        b = UndergroundBar(place=self.p1, serves_cocktails=True)
        b.save()
        with self.assertNumQueries(0):
            self.assertEqual(self.p1.undergroundbar, b)
        b.place = None
        b.save()
        with self.assertNumQueries(0):
            with self.assertRaises(UndergroundBar.DoesNotExist):
                self.p1.undergroundbar
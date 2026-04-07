def test_difference_mixed_srid(self):
        """Testing with mixed SRID (Country has default 4326)."""
        geom = Point(556597.4, 2632018.6, srid=3857)  # Spherical Mercator
        qs = Country.objects.annotate(difference=functions.Difference("mpoly", geom))
        # Oracle does something screwy with the Texas geometry.
        if connection.ops.oracle:
            qs = qs.exclude(name="Texas")
        for c in qs:
            self.assertTrue(c.mpoly.difference(geom).equals(c.difference))
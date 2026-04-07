def test_difference(self):
        geom = Point(5, 23, srid=4326)
        qs = Country.objects.annotate(diff=functions.Difference("mpoly", geom))
        # Oracle does something screwy with the Texas geometry.
        if connection.ops.oracle:
            qs = qs.exclude(name="Texas")

        for c in qs:
            self.assertTrue(c.mpoly.difference(geom).equals(c.diff))
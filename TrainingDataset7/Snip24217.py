def test_reverse_geom(self):
        coords = [(-95.363151, 29.763374), (-95.448601, 29.713803)]
        Track.objects.create(name="Foo", line=LineString(coords))
        track = Track.objects.annotate(reverse_geom=functions.Reverse("line")).get(
            name="Foo"
        )
        coords.reverse()
        self.assertEqual(tuple(coords), track.reverse_geom.coords)
def test_num_points(self):
        coords = [(-95.363151, 29.763374), (-95.448601, 29.713803)]
        Track.objects.create(name="Foo", line=LineString(coords))
        qs = Track.objects.annotate(num_points=functions.NumPoints("line"))
        self.assertEqual(qs.first().num_points, 2)
        mpoly_qs = Country.objects.annotate(num_points=functions.NumPoints("mpoly"))
        if not connection.features.supports_num_points_poly:
            for c in mpoly_qs:
                self.assertIsNone(c.num_points)
            return

        for c in mpoly_qs:
            self.assertEqual(c.mpoly.num_points, c.num_points)

        for c in City.objects.annotate(num_points=functions.NumPoints("point")):
            self.assertEqual(c.num_points, 1)
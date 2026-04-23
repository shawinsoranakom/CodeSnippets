def test_crosses_lookup(self):
        Track.objects.create(name="Line1", line=LineString([(-95, 29), (-60, 0)]))
        self.assertEqual(
            Track.objects.filter(
                line__crosses=LineString([(-95, 0), (-60, 29)])
            ).count(),
            1,
        )
        self.assertEqual(
            Track.objects.filter(
                line__crosses=LineString([(-95, 30), (0, 30)])
            ).count(),
            0,
        )
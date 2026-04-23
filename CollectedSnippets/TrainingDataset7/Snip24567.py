def test02_select_related(self):
        "Testing `select_related` on geographic models (see #7126)."
        qs1 = City.objects.order_by("id")
        qs2 = City.objects.order_by("id").select_related()
        qs3 = City.objects.order_by("id").select_related("location")

        # Reference data for what's in the fixtures.
        cities = (
            ("Aurora", "TX", -97.516111, 33.058333),
            ("Roswell", "NM", -104.528056, 33.387222),
            ("Kecksburg", "PA", -79.460734, 40.18476),
        )

        for qs in (qs1, qs2, qs3):
            for ref, c in zip(cities, qs):
                nm, st, lon, lat = ref
                self.assertEqual(nm, c.name)
                self.assertEqual(st, c.state)
                self.assertAlmostEqual(lon, c.location.point.x, 6)
                self.assertAlmostEqual(lat, c.location.point.y, 6)
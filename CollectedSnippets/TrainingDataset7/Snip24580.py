def test13c_count(self):
        "Testing `Count` aggregate with `.values()`. See #15305."
        qs = (
            Location.objects.filter(id=5)
            .annotate(num_cities=Count("city"))
            .values("id", "point", "num_cities")
        )
        self.assertEqual(1, len(qs))
        self.assertEqual(2, qs[0]["num_cities"])
        self.assertIsInstance(qs[0]["point"], GEOSGeometry)
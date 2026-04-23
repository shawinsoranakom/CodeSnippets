def test_extent(self):
        "Testing `extent` on a table with a single point. See #11827."
        pnt = City.objects.get(name="Pueblo").point
        ref_ext = (pnt.x, pnt.y, pnt.x, pnt.y)
        extent = City.objects.filter(name="Pueblo").aggregate(Extent("point"))[
            "point__extent"
        ]
        for ref_val, val in zip(ref_ext, extent):
            self.assertAlmostEqual(ref_val, val, 4)
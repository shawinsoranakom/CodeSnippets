def test_force_polygon_cw(self):
        rings = (
            ((0, 0), (5, 0), (0, 5), (0, 0)),
            ((1, 1), (1, 3), (3, 1), (1, 1)),
        )
        rhr_rings = (
            ((0, 0), (0, 5), (5, 0), (0, 0)),
            ((1, 1), (3, 1), (1, 3), (1, 1)),
        )
        State.objects.create(name="Foo", poly=Polygon(*rings))
        st = State.objects.annotate(
            force_polygon_cw=functions.ForcePolygonCW("poly")
        ).get(name="Foo")
        self.assertEqual(rhr_rings, st.force_polygon_cw.coords)
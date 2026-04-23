def test_polygon_m_dimension(self):
        geom = OGRGeometry("POLYGON Z ((0 0 0, 10 0 0, 10 10 0, 0 10 0, 0 0 0))")
        self.assertIs(geom.is_measured, False)
        self.assertEqual(
            geom.shell.wkt, "LINEARRING (0 0 0,10 0 0,10 10 0,0 10 0,0 0 0)"
        )

        geom = OGRGeometry("POLYGON M ((0 0 0, 10 0 0, 10 10 0, 0 10 0, 0 0 0))")
        self.assertIs(geom.is_measured, True)
        self.assertEqual(
            geom.shell.wkt, "LINEARRING M (0 0 0,10 0 0,10 10 0,0 10 0,0 0 0)"
        )

        geom = OGRGeometry(
            "POLYGON ZM ((0 0 0 1, 10 0 0 1, 10 10 0 1, 0 10 0 1, 0 0 0 1))"
        )
        self.assertIs(geom.is_measured, True)
        self.assertEqual(
            geom.shell.wkt,
            "LINEARRING ZM (0 0 0 1,10 0 0 1,10 10 0 1,0 10 0 1,0 0 0 1)",
        )

        geom.set_measured(False)
        self.assertEqual(geom.wkt, "POLYGON ((0 0 0,10 0 0,10 10 0,0 10 0,0 0 0))")
        self.assertEqual(
            geom.shell.wkt, "LINEARRING (0 0 0,10 0 0,10 10 0,0 10 0,0 0 0)"
        )
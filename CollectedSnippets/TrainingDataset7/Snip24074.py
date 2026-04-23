def test_get_curve_geometry_no_conversion_possible(self):
        geom = OGRGeometry("LINESTRING (0 0, 1 0, 2 0)")
        geom2 = geom.get_curve_geometry()
        self.assertEqual(geom2.wkt, geom.wkt)
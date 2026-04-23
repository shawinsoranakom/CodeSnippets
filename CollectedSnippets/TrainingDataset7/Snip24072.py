def test_get_linear_geometry_no_conversion_possible(self):
        wkt = "POINT (0 0)"
        geom = OGRGeometry(wkt)
        geom2 = geom.get_linear_geometry()
        self.assertEqual(geom2.wkt, wkt)
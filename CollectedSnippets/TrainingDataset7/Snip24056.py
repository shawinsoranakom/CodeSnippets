def test_empty_point_to_geos(self):
        p = OGRGeometry("POINT EMPTY", srs=4326)
        self.assertEqual(p.geos.ewkt, p.ewkt)
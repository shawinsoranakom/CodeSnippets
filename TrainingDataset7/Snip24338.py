def test_point_reverse(self):
        point = GEOSGeometry("POINT(144.963 -37.8143)", 4326)
        self.assertEqual(point.srid, 4326)
        point.reverse()
        self.assertEqual(point.ewkt, "SRID=4326;POINT (-37.8143 144.963)")
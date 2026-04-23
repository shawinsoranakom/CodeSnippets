def test_linestring_reverse(self):
        line = GEOSGeometry("LINESTRING(144.963 -37.8143,151.2607 -33.887)", 4326)
        self.assertEqual(line.srid, 4326)
        line.reverse()
        self.assertEqual(
            line.ewkt, "SRID=4326;LINESTRING (151.2607 -33.887, 144.963 -37.8143)"
        )
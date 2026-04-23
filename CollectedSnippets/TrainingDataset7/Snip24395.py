def test_from_ewkt(self):
        self.assertEqual(
            GEOSGeometry.from_ewkt("SRID=1;POINT(1 1)"), Point(1, 1, srid=1)
        )
        self.assertEqual(GEOSGeometry.from_ewkt("POINT(1 1)"), Point(1, 1))
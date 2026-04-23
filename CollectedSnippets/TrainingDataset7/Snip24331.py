def test_eq_with_srid(self):
        "Testing non-equivalence with different srids."
        p0 = Point(5, 23)
        p1 = Point(5, 23, srid=4326)
        p2 = Point(5, 23, srid=32632)
        # GEOS
        self.assertNotEqual(p0, p1)
        self.assertNotEqual(p1, p2)
        # EWKT
        self.assertNotEqual(p0, p1.ewkt)
        self.assertNotEqual(p1, p0.ewkt)
        self.assertNotEqual(p1, p2.ewkt)
        # Equivalence with matching SRIDs
        self.assertEqual(p2, p2)
        self.assertEqual(p2, p2.ewkt)
        # WKT contains no SRID so will not equal
        self.assertNotEqual(p2, p2.wkt)
        # SRID of 0
        self.assertEqual(p0, "SRID=0;POINT (5 23)")
        self.assertNotEqual(p1, "SRID=0;POINT (5 23)")
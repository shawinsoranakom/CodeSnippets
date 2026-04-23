def test_fromstr_scientific_wkt(self):
        self.assertEqual(GEOSGeometry("POINT(1.0e-1 1.0e+1)"), Point(0.1, 10))
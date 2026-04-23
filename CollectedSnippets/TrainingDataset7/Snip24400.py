def test_make_valid(self):
        poly = GEOSGeometry("POLYGON((0 0, 0 23, 23 0, 23 23, 0 0))")
        self.assertIs(poly.valid, False)
        valid_poly = poly.make_valid()
        self.assertIs(valid_poly.valid, True)
        self.assertNotEqual(valid_poly, poly)

        valid_poly2 = valid_poly.make_valid()
        self.assertIs(valid_poly2.valid, True)
        self.assertEqual(valid_poly, valid_poly2)
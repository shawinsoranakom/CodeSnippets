def test02_properties(self):
        "Testing Envelope properties."
        e = Envelope(0, 0, 2, 3)
        self.assertEqual(0, e.min_x)
        self.assertEqual(0, e.min_y)
        self.assertEqual(2, e.max_x)
        self.assertEqual(3, e.max_y)
        self.assertEqual((0, 0), e.ll)
        self.assertEqual((2, 3), e.ur)
        self.assertEqual((0, 0, 2, 3), e.tuple)
        self.assertEqual("POLYGON((0.0 0.0,0.0 3.0,2.0 3.0,2.0 0.0,0.0 0.0))", e.wkt)
        self.assertEqual("(0.0, 0.0, 2.0, 3.0)", str(e))
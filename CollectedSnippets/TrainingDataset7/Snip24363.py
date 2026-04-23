def test_covers(self):
        poly = Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)))
        self.assertTrue(poly.covers(Point(5, 5)))
        self.assertFalse(poly.covers(Point(100, 100)))
def test_polygon_comparison(self):
        p1 = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
        p2 = Polygon(((0, 0), (0, 1), (1, 0), (0, 0)))
        self.assertGreater(p1, p2)
        self.assertLess(p2, p1)

        p3 = Polygon(((0, 0), (0, 1), (1, 1), (2, 0), (0, 0)))
        p4 = Polygon(((0, 0), (0, 1), (2, 2), (1, 0), (0, 0)))
        self.assertGreater(p4, p3)
        self.assertLess(p3, p4)
def test_empty_point(self):
        p = Point(srid=4326)
        self.assertEqual(p.ogr.ewkt, p.ewkt)

        self.assertEqual(p.transform(2774, clone=True), Point(srid=2774))
        p.transform(2774)
        self.assertEqual(p, Point(srid=2774))
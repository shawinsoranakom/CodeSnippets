def test_fromwkt(self):
        g = Point(56.811078, 60.608647)
        pt1, pt2 = City.objects.values_list(
            functions.FromWKT(Value(g.wkt)),
            functions.FromWKT(Value(g.wkt), srid=4326),
        )[0]
        self.assertIs(g.equals_exact(pt1, 0.00001), True)
        self.assertIsNone(pt1.srid)
        self.assertEqual(pt2.srid, 4326)
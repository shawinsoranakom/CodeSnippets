def test_multilinestring_with_linearring(self):
        geom = MultiLineString(
            LineString((0, 0), (1, 1), (5, 5)),
            LinearRing((0, 0), (0, 5), (5, 5), (5, 0), (0, 0)),
        )
        obj = Lines.objects.create(geom=geom)
        obj.refresh_from_db()
        self.assertEqual(obj.geom.tuple, geom.tuple)
        self.assertEqual(obj.geom[1].__class__.__name__, "LineString")
        self.assertEqual(obj.geom[0].tuple, geom[0].tuple)
        # LinearRings are transformed to LineString.
        self.assertEqual(obj.geom[1].__class__.__name__, "LineString")
        self.assertEqual(obj.geom[1].tuple, geom[1].tuple)
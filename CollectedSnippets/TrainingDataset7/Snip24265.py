def test_multipointfield(self):
        geom = MultiPoint(Point(1, 1), Point(0, 0))
        obj = Points.objects.create(geom=geom)
        obj.refresh_from_db()
        self.assertEqual(obj.geom, geom)
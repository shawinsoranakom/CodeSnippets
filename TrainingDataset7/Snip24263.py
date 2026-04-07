def test_multilinestringfield(self):
        geom = MultiLineString(
            LineString((0, 0), (1, 1), (5, 5)),
            LineString((0, 0), (0, 5), (5, 5), (5, 0), (0, 0)),
        )
        obj = Lines.objects.create(geom=geom)
        obj.refresh_from_db()
        self.assertEqual(obj.geom.tuple, geom.tuple)
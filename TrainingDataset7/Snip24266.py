def test_geometrycollectionfield(self):
        geom = GeometryCollection(
            Point(2, 2),
            LineString((0, 0), (2, 2)),
            Polygon(LinearRing((0, 0), (0, 5), (5, 5), (5, 0), (0, 0))),
        )
        obj = GeometryCollectionModel.objects.create(geom=geom)
        obj.refresh_from_db()
        self.assertIs(obj.geom.equals(geom), True)
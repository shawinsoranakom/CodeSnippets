def test_collection_dims(self):
        gc = GeometryCollection([])
        self.assertEqual(gc.dims, -1)

        gc = GeometryCollection(Point(0, 0))
        self.assertEqual(gc.dims, 0)

        gc = GeometryCollection(LineString((0, 0), (1, 1)), Point(0, 0))
        self.assertEqual(gc.dims, 1)

        gc = GeometryCollection(
            LineString((0, 0), (1, 1)),
            Polygon(((0, 0), (0, 1), (1, 1), (0, 0))),
            Point(0, 0),
        )
        self.assertEqual(gc.dims, 2)
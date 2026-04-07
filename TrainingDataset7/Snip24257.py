def test_geometryfield(self):
        "Testing the general GeometryField."
        Feature(name="Point", geom=Point(1, 1)).save()
        Feature(name="LineString", geom=LineString((0, 0), (1, 1), (5, 5))).save()
        Feature(
            name="Polygon",
            geom=Polygon(LinearRing((0, 0), (0, 5), (5, 5), (5, 0), (0, 0))),
        ).save()
        Feature(
            name="GeometryCollection",
            geom=GeometryCollection(
                Point(2, 2),
                LineString((0, 0), (2, 2)),
                Polygon(LinearRing((0, 0), (0, 5), (5, 5), (5, 0), (0, 0))),
            ),
        ).save()

        f_1 = Feature.objects.get(name="Point")
        self.assertIsInstance(f_1.geom, Point)
        self.assertEqual((1.0, 1.0), f_1.geom.tuple)
        f_2 = Feature.objects.get(name="LineString")
        self.assertIsInstance(f_2.geom, LineString)
        self.assertEqual(((0.0, 0.0), (1.0, 1.0), (5.0, 5.0)), f_2.geom.tuple)

        f_3 = Feature.objects.get(name="Polygon")
        self.assertIsInstance(f_3.geom, Polygon)
        f_4 = Feature.objects.get(name="GeometryCollection")
        self.assertIsInstance(f_4.geom, GeometryCollection)
        self.assertEqual(f_3.geom, f_4.geom[2])
def test_geometry_type(self):
        test_features = [
            Feature(name="Point", geom=Point(0, 0)),
            Feature(name="LineString", geom=LineString((0, 0), (1, 1))),
            Feature(name="Polygon", geom=Polygon(((0, 0), (1, 0), (1, 1), (0, 0)))),
            Feature(
                name="MultiLineString",
                geom=MultiLineString(
                    LineString((0, 0), (1, 1)), LineString((1, 1), (2, 2))
                ),
            ),
            Feature(
                name="MultiPolygon",
                geom=MultiPolygon(
                    Polygon(((0, 0), (1, 0), (1, 1), (0, 0))),
                    Polygon(((1, 1), (2, 1), (2, 2), (1, 1))),
                ),
            ),
        ]
        expected_results = [
            ("POINT", Point),
            ("LINESTRING", LineString),
            ("POLYGON", Polygon),
            ("MULTILINESTRING", MultiLineString),
            ("MULTIPOLYGON", MultiPolygon),
        ]
        if can_save_multipoint:
            test_features.append(
                Feature(name="MultiPoint", geom=MultiPoint(Point(0, 0), Point(1, 1)))
            )
            expected_results.append(("MULTIPOINT", MultiPoint))
        for test_feature, (geom_type, geom_class) in zip(
            test_features, expected_results, strict=True
        ):
            with self.subTest(geom_type=geom_type, geom=test_feature.geom.wkt):
                test_feature.save()
                obj = (
                    Feature.objects.annotate(
                        geometry_type=functions.GeometryType("geom")
                    )
                    .filter(geom__geom_type=geom_type)
                    .get()
                )
                self.assertIsInstance(obj.geom, geom_class)
                self.assertEqual(obj.geometry_type, geom_type)
def test_empty_geometries(self):
        geometry_classes = [
            Point,
            LineString,
            LinearRing,
            Polygon,
            MultiPoint,
            MultiLineString,
            MultiPolygon,
            GeometryCollection,
        ]
        for klass in geometry_classes:
            g = klass(srid=4326)
            model_class = Feature
            if g.hasz:
                if not connection.features.supports_3d_storage:
                    continue
                else:
                    model_class = ThreeDimensionalFeature
            feature = model_class.objects.create(name=f"Empty {klass.__name__}", geom=g)
            feature.refresh_from_db()
            if klass is LinearRing:
                # LinearRing isn't representable in WKB, so GEOSGeomtry.wkb
                # uses LineString instead.
                g = LineString(srid=4326)
            self.assertEqual(feature.geom, g)
            self.assertEqual(feature.geom.srid, g.srid)
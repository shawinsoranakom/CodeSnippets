def test_geometry_value_annotation_different_srid(self):
        p = Point(1, 1, srid=32140)
        point = City.objects.annotate(p=Value(p, GeometryField(srid=4326))).first().p
        self.assertTrue(point.equals_exact(p.transform(4326, clone=True), 10**-5))
        self.assertEqual(point.srid, 4326)
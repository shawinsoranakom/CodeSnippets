def test_geometry_value_annotation(self):
        p = Point(1, 1, srid=4326)
        point = City.objects.annotate(p=Value(p, GeometryField(srid=4326))).first().p
        self.assertEqual(point, p)
def test_isempty_geometry_empty(self):
        empty = City.objects.create(name="Nowhere", point=Point(srid=4326))
        City.objects.create(name="Somewhere", point=Point(6.825, 47.1, srid=4326))
        self.assertSequenceEqual(
            City.objects.annotate(isempty=functions.IsEmpty("point")).filter(
                isempty=True
            ),
            [empty],
        )
        self.assertSequenceEqual(City.objects.filter(point__isempty=True), [empty])
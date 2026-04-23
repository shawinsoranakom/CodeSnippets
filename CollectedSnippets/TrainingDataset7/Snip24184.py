def test_asgeojson_option_0(self):
        p1 = Point(1, 1, srid=4326)
        p2 = Point(-87.65018, 41.85039, srid=4326)
        obj = ManyPointModel.objects.create(
            point1=p1,
            point2=p2,
            point3=p2.transform(3857, clone=True),
        )
        self.assertJSONEqual(
            ManyPointModel.objects.annotate(geojson=functions.AsGeoJSON("point3"))
            .get(pk=obj.pk)
            .geojson,
            # GeoJSON without CRS.
            json.loads(
                '{"type":"Point","coordinates":[-9757173.40553877, 5138594.87034608]}'
            ),
        )
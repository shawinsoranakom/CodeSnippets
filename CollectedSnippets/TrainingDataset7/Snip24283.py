def test_subquery_annotation(self):
        multifields = MultiFields.objects.create(
            city=City.objects.create(point=Point(1, 1)),
            point=Point(2, 2),
            poly=Polygon.from_bbox((0, 0, 2, 2)),
        )
        qs = MultiFields.objects.annotate(
            city_point=Subquery(
                City.objects.filter(
                    id=OuterRef("city"),
                ).values("point")
            ),
        ).filter(
            city_point__within=F("poly"),
        )
        self.assertEqual(qs.get(), multifields)
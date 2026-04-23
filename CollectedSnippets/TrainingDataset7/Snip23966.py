def test_distance_annotation_group_by(self):
        stx_pnt = self.stx_pnt.transform(
            SouthTexasCity._meta.get_field("point").srid,
            clone=True,
        )
        qs = (
            SouthTexasCity.objects.annotate(
                relative_distance=Case(
                    When(point__distance_lte=(stx_pnt, D(km=20)), then=Value(20)),
                    default=Value(100),
                    output_field=IntegerField(),
                ),
            )
            .values("relative_distance")
            .annotate(count=Count("pk"))
        )
        self.assertCountEqual(
            qs,
            [
                {"relative_distance": 20, "count": 5},
                {"relative_distance": 100, "count": 4},
            ],
        )
def test_distance_order_by(self):
        qs = (
            SouthTexasCity.objects.annotate(
                distance=Distance("point", Point(3, 3, srid=32140))
            )
            .order_by("distance")
            .values_list("name", flat=True)
            .filter(name__in=("San Antonio", "Pearland"))
        )
        self.assertSequenceEqual(qs, ["San Antonio", "Pearland"])
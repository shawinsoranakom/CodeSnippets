def test_distance_function_tolerance(self):
        # Tolerance is greater than distance.
        qs = (
            Interstate.objects.annotate(
                d=Distance(
                    Point(0, 0, srid=3857),
                    Point(1, 1, srid=3857),
                    tolerance=1.5,
                ),
            )
            .filter(d=0)
            .values("pk")
        )
        self.assertIs(qs.exists(), True)
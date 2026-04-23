def test_distance_function_tolerance_escaping(self):
        qs = (
            Interstate.objects.annotate(
                d=Distance(
                    Point(500, 500, srid=3857),
                    Point(0, 0, srid=3857),
                    tolerance="0.05) = 1 OR 1=1 OR (1+1",
                ),
            )
            .filter(d=D(m=1))
            .values("pk")
        )
        msg = "The tolerance parameter has the wrong type"
        with self.assertRaisesMessage(TypeError, msg):
            qs.exists()
def test_distance_function_raw_result(self):
        distance = (
            Interstate.objects.annotate(
                d=Distance(Point(0, 0, srid=4326), Point(0, 1, srid=4326)),
            )
            .first()
            .d
        )
        self.assertEqual(distance, 1)
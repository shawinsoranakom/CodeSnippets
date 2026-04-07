def test_distance_function_raw_result_d_lookup(self):
        qs = Interstate.objects.annotate(
            d=Distance(Point(0, 0, srid=4326), Point(0, 1, srid=4326)),
        ).filter(d=D(m=1))
        msg = "Distance measure is supplied, but units are unknown for result."
        with self.assertRaisesMessage(ValueError, msg):
            list(qs)
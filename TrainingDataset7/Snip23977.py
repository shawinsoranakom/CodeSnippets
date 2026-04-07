def test_distance_function_d_lookup(self):
        qs = Interstate.objects.annotate(
            d=Distance(Point(0, 0, srid=3857), Point(0, 1, srid=3857)),
        ).filter(d=D(m=1))
        self.assertTrue(qs.exists())
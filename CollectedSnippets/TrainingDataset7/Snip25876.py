def test_in_lookup_in_filter(self):
        test_cases = [
            ((), ()),
            ((1942,), (self.s1,)),
            ((1842,), (self.s2,)),
            ((2042,), (self.s3,)),
            ((1942, 1842), (self.s1, self.s2)),
            ((1942, 2042), (self.s1, self.s3)),
            ((1842, 2042), (self.s2, self.s3)),
            ((1942, 1942, 1942), (self.s1,)),
            ((1942, 2042, 1842), (self.s1, self.s2, self.s3)),
        ]

        for years, seasons in test_cases:
            with self.subTest(years=years, seasons=seasons):
                self.assertSequenceEqual(
                    Season.objects.filter(In(F("year"), years)).order_by("pk"), seasons
                )
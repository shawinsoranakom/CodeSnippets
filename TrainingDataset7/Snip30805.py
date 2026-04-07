def test_to_field(self):
        self.assertSequenceEqual(
            Food.objects.exclude(eaten__meal="dinner"),
            [self.f2],
        )
        self.assertSequenceEqual(
            Job.objects.exclude(responsibilities__description="Playing golf"),
            [self.j2],
        )
        self.assertSequenceEqual(
            Responsibility.objects.exclude(jobs__name="Manager"),
            [self.r2],
        )
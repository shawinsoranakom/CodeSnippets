def test_duration_with_datetime(self):
        # Exclude e1 which has very high precision so we can test this on all
        # backends regardless of whether or not it supports
        # microsecond_precision.
        over_estimate = (
            Experiment.objects.exclude(name="e1")
            .filter(
                completed__gt=self.stime + F("estimated_time"),
            )
            .order_by("name")
        )
        self.assertQuerySetEqual(over_estimate, ["e3", "e4", "e5"], lambda e: e.name)
def test_negative_timedelta_update(self):
        # subtract 30 seconds, 30 minutes, 2 hours and 2 days
        experiments = (
            Experiment.objects.filter(name="e0")
            .annotate(
                start_sub_seconds=F("start") + datetime.timedelta(seconds=-30),
            )
            .annotate(
                start_sub_minutes=F("start_sub_seconds")
                + datetime.timedelta(minutes=-30),
            )
            .annotate(
                start_sub_hours=F("start_sub_minutes") + datetime.timedelta(hours=-2),
            )
            .annotate(
                new_start=F("start_sub_hours") + datetime.timedelta(days=-2),
            )
        )
        expected_start = datetime.datetime(2010, 6, 23, 9, 45, 0)
        # subtract 30 microseconds
        experiments = experiments.annotate(
            new_start=F("new_start") + datetime.timedelta(microseconds=-30)
        )
        expected_start += datetime.timedelta(microseconds=+746970)
        experiments.update(start=F("new_start"))
        e0 = Experiment.objects.get(name="e0")
        self.assertEqual(e0.start, expected_start)
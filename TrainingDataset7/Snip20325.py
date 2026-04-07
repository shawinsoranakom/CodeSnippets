def test_cast_to_duration(self):
        duration = datetime.timedelta(days=1, seconds=2, microseconds=3)
        DTModel.objects.create(duration=duration)
        dtm = DTModel.objects.annotate(
            cast_duration=Cast("duration", models.DurationField()),
            cast_neg_duration=Cast(-duration, models.DurationField()),
        ).get()
        self.assertEqual(dtm.cast_duration, duration)
        self.assertEqual(dtm.cast_neg_duration, -duration)
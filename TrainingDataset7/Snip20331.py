def test_cast_from_python_to_datetime(self):
        now = datetime.datetime.now()
        dates = Author.objects.annotate(cast_datetime=Cast(now, models.DateTimeField()))
        time_precision = datetime.timedelta(
            microseconds=10 ** (6 - connection.features.time_cast_precision)
        )
        self.assertAlmostEqual(dates.get().cast_datetime, now, delta=time_precision)
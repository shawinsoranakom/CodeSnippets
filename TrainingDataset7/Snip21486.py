def test_duration_with_datetime_microseconds(self):
        delta = datetime.timedelta(microseconds=8999999999999999)
        qs = Experiment.objects.annotate(
            dt=ExpressionWrapper(
                F("start") + delta,
                output_field=DateTimeField(),
            )
        )
        for e in qs:
            self.assertEqual(e.dt, e.start + delta)
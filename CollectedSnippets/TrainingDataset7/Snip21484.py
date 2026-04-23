def test_datetime_subtraction_microseconds(self):
        delta = datetime.timedelta(microseconds=8999999999999999)
        Experiment.objects.update(end=F("start") + delta)
        qs = Experiment.objects.annotate(delta=F("end") - F("start"))
        for e in qs:
            self.assertEqual(e.delta, delta)
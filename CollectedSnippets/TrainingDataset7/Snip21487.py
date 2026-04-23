def test_date_minus_duration(self):
        more_than_4_days = Experiment.objects.filter(
            assigned__lt=F("completed") - Value(datetime.timedelta(days=4))
        )
        self.assertQuerySetEqual(more_than_4_days, ["e3", "e4", "e5"], lambda e: e.name)
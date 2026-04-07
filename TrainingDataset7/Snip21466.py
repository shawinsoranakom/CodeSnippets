def test_date_comparison(self):
        for i, days in enumerate(self.days_long):
            test_set = [
                e.name
                for e in Experiment.objects.filter(completed__lt=F("assigned") + days)
            ]
            self.assertEqual(test_set, self.expnames[:i])

            test_set = [
                e.name
                for e in Experiment.objects.filter(completed__lte=F("assigned") + days)
            ]
            self.assertEqual(test_set, self.expnames[: i + 1])
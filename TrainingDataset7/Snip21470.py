def test_mixed_comparisons1(self):
        for i, delay in enumerate(self.delays):
            test_set = [
                e.name
                for e in Experiment.objects.filter(assigned__gt=F("start") - delay)
            ]
            self.assertEqual(test_set, self.expnames[:i])

            test_set = [
                e.name
                for e in Experiment.objects.filter(assigned__gte=F("start") - delay)
            ]
            self.assertEqual(test_set, self.expnames[: i + 1])
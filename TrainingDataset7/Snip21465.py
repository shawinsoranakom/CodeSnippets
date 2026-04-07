def test_exclude(self):
        for i, delta in enumerate(self.deltas):
            test_set = [
                e.name for e in Experiment.objects.exclude(end__lt=F("start") + delta)
            ]
            self.assertEqual(test_set, self.expnames[i:])

            test_set = [
                e.name for e in Experiment.objects.exclude(end__lte=F("start") + delta)
            ]
            self.assertEqual(test_set, self.expnames[i + 1 :])
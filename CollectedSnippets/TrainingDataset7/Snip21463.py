def test_delta_add(self):
        for i, delta in enumerate(self.deltas):
            test_set = [
                e.name for e in Experiment.objects.filter(end__lt=F("start") + delta)
            ]
            self.assertEqual(test_set, self.expnames[:i])

            test_set = [
                e.name for e in Experiment.objects.filter(end__lt=delta + F("start"))
            ]
            self.assertEqual(test_set, self.expnames[:i])

            test_set = [
                e.name for e in Experiment.objects.filter(end__lte=F("start") + delta)
            ]
            self.assertEqual(test_set, self.expnames[: i + 1])
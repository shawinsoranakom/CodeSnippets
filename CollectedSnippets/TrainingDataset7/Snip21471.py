def test_mixed_comparisons2(self):
        for i, delay in enumerate(self.delays):
            delay = datetime.timedelta(delay.days)
            test_set = [
                e.name
                for e in Experiment.objects.filter(start__lt=F("assigned") + delay)
            ]
            self.assertEqual(test_set, self.expnames[:i])

            test_set = [
                e.name
                for e in Experiment.objects.filter(
                    start__lte=F("assigned") + delay + datetime.timedelta(1)
                )
            ]
            self.assertEqual(test_set, self.expnames[: i + 1])
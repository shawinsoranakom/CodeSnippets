def test_delta_update(self):
        for delta in self.deltas:
            exps = Experiment.objects.all()
            expected_durations = [e.duration() for e in exps]
            expected_starts = [e.start + delta for e in exps]
            expected_ends = [e.end + delta for e in exps]

            Experiment.objects.update(start=F("start") + delta, end=F("end") + delta)
            exps = Experiment.objects.all()
            new_starts = [e.start for e in exps]
            new_ends = [e.end for e in exps]
            new_durations = [e.duration() for e in exps]
            self.assertEqual(expected_starts, new_starts)
            self.assertEqual(expected_ends, new_ends)
            self.assertEqual(expected_durations, new_durations)
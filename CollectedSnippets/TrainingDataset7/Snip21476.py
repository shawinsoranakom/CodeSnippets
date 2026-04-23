def test_duration_expressions(self):
        for delta in self.deltas:
            qs = Experiment.objects.annotate(duration=F("estimated_time") + delta)
            for obj in qs:
                self.assertEqual(obj.duration, obj.estimated_time + delta)
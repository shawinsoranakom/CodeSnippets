def test_datetime_and_durationfield_addition_with_filter(self):
        test_set = Experiment.objects.filter(end=F("start") + F("estimated_time"))
        self.assertGreater(test_set.count(), 0)
        self.assertEqual(
            [e.name for e in test_set],
            [
                e.name
                for e in Experiment.objects.all()
                if e.end == e.start + e.estimated_time
            ],
        )
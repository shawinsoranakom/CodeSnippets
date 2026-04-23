def test_multiple_transforms_in_values(self):
        self.assertSequenceEqual(
            Experiment.objects.values("end__date__month"),
            [{"end__date__month": 6}],
        )
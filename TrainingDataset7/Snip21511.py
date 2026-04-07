def test_transform_in_values(self):
        self.assertSequenceEqual(
            Experiment.objects.values("assigned__month"),
            [{"assigned__month": 6}],
        )
def test_ticket8283(self):
        # Checking that applying filters after a disjunction works correctly.
        self.assertSequenceEqual(
            (
                ExtraInfo.objects.filter(note=self.n1)
                | ExtraInfo.objects.filter(info="e2")
            ).filter(note=self.n1),
            [self.e1],
        )
        self.assertSequenceEqual(
            (
                ExtraInfo.objects.filter(info="e2")
                | ExtraInfo.objects.filter(note=self.n1)
            ).filter(note=self.n1),
            [self.e1],
        )
def test_join_trimming_reverse(self):
        self.assertSequenceEqual(
            self.bob.group_set.filter(membership__price=50),
            [self.roll],
        )
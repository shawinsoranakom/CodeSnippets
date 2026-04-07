def assertQuerySetEqualReversible(self, queryset, sequence):
        self.assertSequenceEqual(queryset, sequence)
        self.assertSequenceEqual(queryset.reverse(), list(reversed(sequence)))
def test_in_lookup_allows_F_expressions_and_expressions_for_integers(self):
        # __in lookups can use F() expressions for integers.
        queryset = Company.objects.filter(num_employees__in=([F("num_chairs") - 10]))
        self.assertSequenceEqual(queryset, [self.c5060])
        self.assertCountEqual(
            Company.objects.filter(
                num_employees__in=([F("num_chairs") - 10, F("num_chairs") + 10])
            ),
            [self.c5040, self.c5060],
        )
        self.assertCountEqual(
            Company.objects.filter(
                num_employees__in=(
                    [F("num_chairs") - 10, F("num_chairs"), F("num_chairs") + 10]
                )
            ),
            [self.c5040, self.c5050, self.c5060],
        )
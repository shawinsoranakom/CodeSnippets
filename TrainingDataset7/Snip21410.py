def test_range_lookup_allows_F_expressions_and_expressions_for_integers(self):
        # Range lookups can use F() expressions for integers.
        Company.objects.filter(num_employees__exact=F("num_chairs"))
        self.assertCountEqual(
            Company.objects.filter(num_employees__range=(F("num_chairs"), 100)),
            [self.c5020, self.c5040, self.c5050],
        )
        self.assertCountEqual(
            Company.objects.filter(
                num_employees__range=(F("num_chairs") - 10, F("num_chairs") + 10)
            ),
            [self.c5040, self.c5050, self.c5060],
        )
        self.assertCountEqual(
            Company.objects.filter(num_employees__range=(F("num_chairs") - 10, 100)),
            [self.c5020, self.c5040, self.c5050, self.c5060],
        )
        self.assertCountEqual(
            Company.objects.filter(num_employees__range=(1, 100)),
            [self.c5020, self.c5040, self.c5050, self.c5060, self.c99300],
        )
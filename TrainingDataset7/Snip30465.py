def assertNumbersEqual(self, queryset, expected_numbers, ordered=True):
        self.assertQuerySetEqual(
            queryset, expected_numbers, operator.attrgetter("num"), ordered
        )
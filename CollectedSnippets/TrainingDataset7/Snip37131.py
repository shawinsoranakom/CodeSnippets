def test_empty_in(self):
        self.assertCountEqual(
            Number.objects.filter(Q(pk__in=[]) ^ Q(num__gte=5)),
            self.numbers[5:],
        )
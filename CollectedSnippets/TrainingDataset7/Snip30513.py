def test_union_in_with_ordering_and_slice(self):
        qs1 = Number.objects.filter(num__gt=7).order_by("num")[:1]
        qs2 = Number.objects.filter(num__lt=2).order_by("-num")[:1]
        self.assertNumbersEqual(
            Number.objects.exclude(id__in=qs1.union(qs2).values("id")),
            [0, 2, 3, 4, 5, 6, 7, 9],
            ordered=False,
        )
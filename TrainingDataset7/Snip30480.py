def test_union_nested(self):
        qs1 = Number.objects.all()
        qs2 = qs1.union(qs1)
        self.assertNumbersEqual(
            qs1.union(qs2),
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            ordered=False,
        )
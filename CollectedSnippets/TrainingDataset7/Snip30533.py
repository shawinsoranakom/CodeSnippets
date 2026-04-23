def test_order_by_same_type(self):
        qs = Number.objects.all()
        union = qs.union(qs)
        numbers = list(range(10))
        self.assertNumbersEqual(union.order_by("num"), numbers)
        self.assertNumbersEqual(union.order_by("other_num"), reversed(numbers))
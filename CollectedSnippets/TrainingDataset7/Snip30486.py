def test_empty_qs_union_with_ordered_qs(self):
        qs1 = Number.objects.order_by("num")
        qs2 = Number.objects.none().union(qs1).order_by("num")
        self.assertEqual(list(qs1), list(qs2))
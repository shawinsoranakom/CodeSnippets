def test_lt(self):
        qs = self.queryset.filter(qty_needed__lt=0)
        self.assertCountEqual(qs, [self.p1])
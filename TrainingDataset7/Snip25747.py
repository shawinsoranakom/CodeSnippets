def test_gt(self):
        qs = self.queryset.filter(qty_needed__gt=0)
        self.assertCountEqual(qs, [self.p3])
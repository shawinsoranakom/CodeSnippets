def test_filter_deferred(self):
        qs = Happening.objects.all()
        qs._defer_next_filter = True
        qs = qs.filter(id=0)
        self.assert_pickles(qs)
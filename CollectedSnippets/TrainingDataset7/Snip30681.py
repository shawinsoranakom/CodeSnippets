def test_tickets_3045_3288(self):
        # Once upon a time, select_related() with circular relations would loop
        # infinitely if you forgot to specify "depth". Now we set an arbitrary
        # default upper bound.
        self.assertSequenceEqual(X.objects.all(), [])
        self.assertSequenceEqual(X.objects.select_related(), [])
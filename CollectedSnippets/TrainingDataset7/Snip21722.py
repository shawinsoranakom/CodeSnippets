def test_regression_8063(self):
        """
        Regression test for #8063: limiting a query shouldn't discard any
        extra() bits.
        """
        qs = User.objects.extra(where=["id=%s"], params=[self.u.id])
        self.assertSequenceEqual(qs, [self.u])
        self.assertSequenceEqual(qs[:1], [self.u])
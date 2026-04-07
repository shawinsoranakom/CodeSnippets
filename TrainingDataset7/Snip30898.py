def test_context_manager(self):
        """
        _avoid_cloning() makes modifications apply to the original QuerySet.
        """
        qs = SimpleCategory.objects.all()
        with qs._avoid_cloning():
            qs2 = qs.filter(name__in={"first", "second"}).exclude(name="second")
        self.assertIs(qs2, qs)
        qs3 = qs2.exclude(name__in={"third", "fourth"})
        # qs3 is not a mutation of qs2 (which is actually also qs) but a new
        # instance entirely.
        self.assertIsNot(qs3, qs)
        self.assertIsNot(qs3, qs2)
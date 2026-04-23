def test_explicit_toggling(self):
        qs = SimpleCategory.objects.filter(name__in={"first", "second"})
        qs2 = qs._disable_cloning()
        # The _disable_cloning() method doesn't return a new QuerySet, but
        # toggles the value on the current instance. qs2 can be ignored.
        self.assertIs(qs2, qs)
        qs3 = qs.filter(name__in={"first", "second"})
        qs3 = qs3.exclude(name="second")
        qs3._enable_cloning()
        # These are still both references to the same QuerySet, despite
        # re-binding as if they were normal chained operations providing new
        # QuerySet instances.
        self.assertIs(qs3, qs)
        qs3 = qs3.filter(name="second")
        # Cloning has been re-enabled so subsequent operations yield a new
        # QuerySet. qs3 is now all of the filters applied to qs + an additional
        # filter.
        self.assertIsNot(qs3, qs)
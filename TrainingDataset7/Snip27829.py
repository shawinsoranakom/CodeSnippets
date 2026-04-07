def test_lookup_really_big_value(self):
        """
        Really big values can be used in a filter statement.
        """
        # This should not crash.
        self.assertSequenceEqual(Foo.objects.filter(d__gte=100000000000), [])
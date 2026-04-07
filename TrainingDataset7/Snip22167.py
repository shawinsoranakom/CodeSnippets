def test_dumpdata_proxy_with_concrete(self):
        """
        A warning isn't displayed if a proxy model is dumped with its concrete
        parent.
        """
        spy = ProxySpy.objects.create(name="Paul")

        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            self._dumpdata_assert(
                ["fixtures.ProxySpy", "fixtures.Spy"],
                '[{"pk": %d, "model": "fixtures.spy", '
                '"fields": {"cover_blown": false}}]' % spy.pk,
            )
        self.assertEqual(len(warning_list), 0)
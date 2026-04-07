def test_dumpdata_with_filtering_manager(self):
        spy1 = Spy.objects.create(name="Paul")
        spy2 = Spy.objects.create(name="Alex", cover_blown=True)
        self.assertSequenceEqual(Spy.objects.all(), [spy1])
        # Use the default manager
        self._dumpdata_assert(
            ["fixtures.Spy"],
            '[{"pk": %d, "model": "fixtures.spy", "fields": {"cover_blown": false}}]'
            % spy1.pk,
        )
        # Dump using Django's base manager. Should return all objects,
        # even those normally filtered by the manager
        self._dumpdata_assert(
            ["fixtures.Spy"],
            '[{"pk": %d, "model": "fixtures.spy", "fields": {"cover_blown": true}}, '
            '{"pk": %d, "model": "fixtures.spy", "fields": {"cover_blown": false}}]'
            % (spy2.pk, spy1.pk),
            use_base_manager=True,
        )
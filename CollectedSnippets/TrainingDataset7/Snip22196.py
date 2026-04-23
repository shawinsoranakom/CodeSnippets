def test_forward_reference_m2m_natural_key(self):
        management.call_command(
            "loaddata",
            "forward_reference_m2m_natural_key.json",
            verbosity=0,
        )
        self.assertEqual(NaturalKeyThing.objects.count(), 3)
        t1 = NaturalKeyThing.objects.get_by_natural_key("t1")
        self.assertSequenceEqual(
            t1.other_things.order_by("key").values_list("key", flat=True),
            ["t2", "t3"],
        )
        self._dumpdata_assert(
            ["fixtures"],
            '[{"model": "fixtures.naturalkeything", '
            '"fields": {"key": "t1", "other_thing": null, '
            '"other_things": [["t2"], ["t3"]]}}, '
            '{"model": "fixtures.naturalkeything", '
            '"fields": {"key": "t2", "other_thing": null, "other_things": []}}, '
            '{"model": "fixtures.naturalkeything", '
            '"fields": {"key": "t3", "other_thing": null, "other_things": []}}]',
            natural_primary_keys=True,
            natural_foreign_keys=True,
        )